"""
Call State Management Service
Handles call state sync, reconnection, and prevents stuck states
"""

import json
import asyncio
import logging
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
from .message_models import Call

logger = logging.getLogger(__name__)

class CallStateManager:
    def __init__(self):
        self.channel_layer = get_channel_layer()
        self.active_calls = {}  # call_id -> {'disconnected_users': set(), 'last_activity': timestamp}
        
    def sync_call_state(self, call_id, user_id, status):
        """Sync call state across all participants"""
        try:
            call = Call.objects.get(call_id=call_id)
            
            # Update call status
            old_status = call.status
            call.status = status
            
            if status == 'answered' and not call.answered_at:
                call.answered_at = timezone.now()
            elif status == 'ended' and not call.ended_at:
                call.ended_at = timezone.now()
                if call.answered_at:
                    call.duration = (timezone.now() - call.answered_at).total_seconds()
                    
            call.save()
            
            # Only broadcast if status actually changed
            if old_status != status:
                participants = [call.caller.id]
                if call.receiver:
                    participants.append(call.receiver.id)
                    
                for participant_id in participants:
                    async_to_sync(self.channel_layer.group_send)(
                        f"call_user_{participant_id}",
                        {
                            'type': 'call_state_sync',
                            'call_id': call_id,
                            'status': status,
                            'updated_by': user_id,
                            'timestamp': timezone.now().isoformat()
                        }
                    )
                    
        except Call.DoesNotExist:
            logger.error(f"Call {call_id} not found for state sync")
        except Exception as e:
            logger.error(f"Error syncing call state: {e}")
    
    def handle_disconnect(self, call_id, user_id):
        """Handle user disconnect - start reconnect timer"""
        if call_id not in self.active_calls:
            self.active_calls[call_id] = {
                'disconnected_users': set(),
                'last_activity': timezone.now()
            }
            
        self.active_calls[call_id]['disconnected_users'].add(user_id)
        
        # Start reconnect timer in background
        import threading
        timer = threading.Timer(30.0, self._handle_reconnect_timeout, [call_id, user_id])
        timer.start()
    
    def _handle_reconnect_timeout(self, call_id, user_id):
        """Handle reconnect timeout - end call if user didn't reconnect"""
        if (call_id in self.active_calls and 
            user_id in self.active_calls[call_id]['disconnected_users']):
            
            # User didn't reconnect - end call
            self.sync_call_state(call_id, user_id, 'ended')
            
            # Clean up
            if call_id in self.active_calls:
                del self.active_calls[call_id]
    
    def handle_reconnect(self, call_id, user_id):
        """Handle user reconnection"""
        if call_id in self.active_calls:
            self.active_calls[call_id]['disconnected_users'].discard(user_id)
            self.active_calls[call_id]['last_activity'] = timezone.now()
            
            # Send current call state
            try:
                call = Call.objects.get(call_id=call_id)
                participants = [call.caller.id]
                if call.receiver:
                    participants.append(call.receiver.id)
                    
                async_to_sync(self.channel_layer.group_send)(
                    f"call_user_{user_id}",
                    {
                        'type': 'call_state_restore',
                        'call_id': call_id,
                        'status': call.status,
                        'participants': participants,
                        'duration': call.duration or 0
                    }
                )
            except Call.DoesNotExist:
                logger.error(f"Call {call_id} not found for reconnect")
            except Exception as e:
                logger.error(f"Error handling reconnect: {e}")

# Global instance
call_state_manager = CallStateManager()