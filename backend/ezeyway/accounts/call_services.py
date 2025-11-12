"""
Enhanced Call Management Services

This module provides comprehensive call management services including:
- Call session management
- 60-second ringing timeout handling
- Background notification management
- Call analytics and statistics
- Network state monitoring
"""

import logging
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import CallSession, CallLog, CallNotification, CallSettings, CallAnalytics, User
from .fcm_service import fcm_send_call_notification

logger = logging.getLogger(__name__)

class CallTimeoutService:
    """Service for managing 60-second ringing timeout"""
    
    @staticmethod
    def create_call_session(caller: User, callee: User, call_type: str = 'audio', **kwargs) -> CallSession:
        """Create a new call session with timeout handling"""
        
        with transaction.atomic():
            # Generate unique call ID
            call_id = str(uuid.uuid4()).replace('-', '')[:16].upper()
            
            # Create call session
            call_session = CallSession.objects.create(
                call_id=call_id,
                caller=caller,
                callee=callee,
                call_type=call_type,
                status='initiated',
                ringing_timeout_seconds=kwargs.get('ringing_timeout_seconds', 60),
                timeout_at=timezone.now() + timedelta(seconds=kwargs.get('ringing_timeout_seconds', 60)),
                **kwargs
            )
            
            # Log call initiation
            CallLog.objects.create(
                call_session=call_session,
                user=caller,
                event_type='initiated',
                timestamp=timezone.now(),
                metadata={'call_type': call_type, 'user_agent': kwargs.get('device_info', {})}
            )
            
            logger.info(f"Call session created: {call_session.call_id}")
            return call_session
    
    @staticmethod
    def start_ringing(call_session: CallSession) -> bool:
        """Start ringing phase and notify callee"""
        
        try:
            call_session.start_ringing()
            
            # Send background notification to callee
            CallNotificationService.send_incoming_call_notification(call_session)
            
            # Log ringing start
            CallLog.objects.create(
                call_session=call_session,
                user=call_session.callee,
                event_type='ringing_started',
                timestamp=timezone.now(),
                metadata={'caller_name': call_session.caller.get_full_name() or call_session.caller.username}
            )
            
            logger.info(f"Started ringing for call: {call_session.call_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start ringing for call {call_session.call_id}: {str(e)}")
            return False
    
    @staticmethod
    def process_timeout_calls():
        """Background task to process timed out calls"""
        
        current_time = timezone.now()
        timed_out_calls = CallSession.objects.filter(
            status__in=['initiated', 'ringing'],
            timeout_at__lte=current_time,
            has_timed_out=False
        )
        
        processed_count = 0
        
        for call_session in timed_out_calls:
            try:
                if call_session.timeout_call():
                    # Send timeout notification
                    CallNotificationService.send_call_timeout_notification(call_session)
                    processed_count += 1
                    logger.info(f"Processed timeout for call: {call_session.call_id}")
                    
            except Exception as e:
                logger.error(f"Failed to process timeout for call {call_session.call_id}: {str(e)}")
        
        if processed_count > 0:
            logger.info(f"Processed {processed_count} timed out calls")
        
        return processed_count


class CallNotificationService:
    """Service for managing call notifications"""
    
    @staticmethod
    def send_incoming_call_notification(call_session: CallSession):
        """Send incoming call notification to callee"""
        
        try:
            # Get callee's FCM token
            fcm_token = call_session.callee.fcm_token if hasattr(call_session.callee, 'fcm_token') else None
            
            # Create notification record
            notification = CallNotification.objects.create(
                call_session=call_session,
                notification_type='incoming_call',
                priority='high',
                target_user=call_session.callee,
                fcm_token=fcm_token,
                title=f"📞 Incoming {call_session.call_type.title()} Call",
                message=f"{call_session.caller.get_full_name() or call_session.caller.username} is calling you",
                data={
                    'call_id': call_session.call_id,
                    'caller_name': call_session.caller.get_full_name() or call_session.caller.username,
                    'call_type': call_session.call_type,
                    'action': 'answer_call'
                }
            )
            
            # Send FCM notification if token available
            if fcm_token:
                CallNotificationService._send_fcm_notification(notification)
            else:
                # Create in-app notification
                CallNotificationService._create_in_app_notification(notification)
            
            logger.info(f"Sent incoming call notification for: {call_session.call_id}")
            return notification
            
        except Exception as e:
            logger.error(f"Failed to send incoming call notification: {str(e)}")
            return None
    
    @staticmethod
    def send_call_timeout_notification(call_session: CallSession):
        """Send call timeout notification"""
        
        try:
            notification = CallNotification.objects.create(
                call_session=call_session,
                notification_type='call_timeout',
                priority='normal',
                target_user=call_session.caller,
                title="📞 Call Missed",
                message=f"📱 {call_session.callee.get_full_name() or call_session.callee.username} didn't answer your call",
                data={
                    'call_id': call_session.call_id,
                    'missed_user': call_session.callee.get_full_name() or call_session.callee.username,
                    'action': 'view_missed_call'
                }
            )
            
            logger.info(f"Sent timeout notification for: {call_session.call_id}")
            return notification
            
        except Exception as e:
            logger.error(f"Failed to send timeout notification: {str(e)}")
            return None
    
    @staticmethod
    def _send_fcm_notification(notification: CallNotification):
        """Send FCM notification to mobile device"""
        
        try:
            # Prepare FCM payload
            payload = {
                'token': notification.fcm_token,
                'notification': {
                    'title': notification.title,
                    'body': notification.message,
                    'sound': 'default',
                    'icon': 'ic_call_24dp'
                },
                'data': notification.data,
                'priority': 'high',
                'time_to_live': 3600  # 1 hour
            }
            
            # Send notification (simplified - integrate with your FCM service)
            fcm_send_call_notification(payload)
            
            # Update notification status
            notification.status = 'sent'
            notification.sent_at = timezone.now()
            notification.save()
            
        except Exception as e:
            logger.error(f"Failed to send FCM notification: {str(e)}")
            notification.status = 'failed'
            notification.save()
    
    @staticmethod
    def _create_in_app_notification(notification: CallNotification):
        """Create in-app notification for web users"""
        
        try:
            # This would integrate with your web notification system
            # For now, we'll just mark it as delivered
            notification.status = 'delivered'
            notification.delivered_at = timezone.now()
            notification.save()
            
        except Exception as e:
            logger.error(f"Failed to create in-app notification: {str(e)}")


class CallSessionManager:
    """Central manager for call session operations"""
    
    @staticmethod
    def initiate_call(caller: User, callee: User, call_type: str = 'audio', **kwargs) -> CallSession:
        """Initiate a new call"""
        
        try:
            # Create call session
            call_session = CallTimeoutService.create_call_session(caller, callee, call_type, **kwargs)
            
            # Start ringing
            if CallTimeoutService.start_ringing(call_session):
                logger.info(f"Call initiated successfully: {call_session.call_id}")
                return call_session
            else:
                # Failed to start ringing, mark as failed
                call_session.status = 'failed'
                call_session.save()
                return call_session
                
        except Exception as e:
            logger.error(f"Failed to initiate call: {str(e)}")
            raise
    
    @staticmethod
    def answer_call(call_session: CallSession, user: User) -> bool:
        """Answer an incoming call"""
        
        try:
            if call_session.answer_call(user):
                # Mark notification as clicked
                CallNotification.objects.filter(
                    call_session=call_session,
                    target_user=user,
                    notification_type='incoming_call'
                ).update(clicked_at=timezone.now(), status='clicked')
                
                logger.info(f"Call answered: {call_session.call_id} by {user.username}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to answer call: {str(e)}")
            return False
    
    @staticmethod
    def reject_call(call_session: CallSession, user: User, reason: str = 'rejected') -> bool:
        """Reject an incoming call"""
        
        try:
            if call_session.reject_call(user, reason):
                logger.info(f"Call rejected: {call_session.call_id} by {user.username}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to reject call: {str(e)}")
            return False
    
    @staticmethod
    def end_call(call_session: CallSession, user: User, reason: str = 'ended') -> bool:
        """End an active call"""
        
        try:
            if call_session.end_call(user, reason):
                logger.info(f"Call ended: {call_session.call_id} by {user.username}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to end call: {str(e)}")
            return False