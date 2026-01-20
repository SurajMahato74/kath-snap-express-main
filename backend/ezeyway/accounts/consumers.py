import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .message_models import Conversation, Message, Call
from .models import VendorProfile
from channels.layers import get_channel_layer
import logging
from django.db import OperationalError
logger = logging.getLogger(__name__)

User = get_user_model()

class MessageConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            await self.close()
            return
        
        self.user_group_name = f"user_{self.user.id}"
        print(f"DEBUG: WebSocket connecting for user {self.user.id}, joining group {self.user_group_name}")

        # Join user group
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        print(f"DEBUG: Joined group {self.user_group_name}")

        await self.accept()
        print(f"DEBUG: WebSocket accepted for user {self.user.id}")
        
        # Send online status
        await self.channel_layer.group_send(
            f"user_status",
            {
                'type': 'user_status',
                'user_id': self.user.id,
                'status': 'online'
            }
        )

    async def disconnect(self, close_code):
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
            
            # Send offline status
            await self.channel_layer.group_send(
                f"user_status",
                {
                    'type': 'user_status',
                    'user_id': self.user.id,
                    'status': 'offline'
                }
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'message':
                await self.handle_message(data)
            elif message_type == 'typing':
                await self.handle_typing(data)
            elif message_type == 'message_read':
                await self.handle_message_read(data)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON'
            }))

    async def handle_message(self, data):
        conversation_id = data.get('conversation_id')
        content = data.get('content')
        
        if not conversation_id or not content:
            return
        
        # Save message to database
        message = await self.save_message(conversation_id, content)
        if not message:
            return
        
        # Get conversation participants
        participants = await self.get_conversation_participants(conversation_id)
        
        # Send message to all participants
        for participant_id in participants:
            await self.channel_layer.group_send(
                f"user_{participant_id}",
                {
                    'type': 'new_message',
                    'message': {
                        'id': message.id,
                        'conversation_id': conversation_id,
                        'sender_id': self.user.id,
                        'sender_name': self.user.username,
                        'content': content,
                        'created_at': message.created_at.isoformat(),
                        'message_type': 'text'
                    }
                }
            )

    async def handle_typing(self, data):
        conversation_id = data.get('conversation_id')
        is_typing = data.get('is_typing', False)
        
        if not conversation_id:
            return
        
        participants = await self.get_conversation_participants(conversation_id)
        
        # Send typing indicator to other participants
        for participant_id in participants:
            if participant_id != self.user.id:
                await self.channel_layer.group_send(
                    f"user_{participant_id}",
                    {
                        'type': 'typing_indicator',
                        'conversation_id': conversation_id,
                        'user_id': self.user.id,
                        'username': self.user.username,
                        'is_typing': is_typing
                    }
                )

    async def handle_message_read(self, data):
        message_id = data.get('message_id')
        if not message_id:
            return
        
        # Mark message as read
        await self.mark_message_read(message_id)
        
        # Get message sender
        sender_id = await self.get_message_sender(message_id)
        if sender_id and sender_id != self.user.id:
            await self.channel_layer.group_send(
                f"user_{sender_id}",
                {
                    'type': 'message_read_receipt',
                    'message_id': message_id,
                    'read_by': self.user.id,
                    'read_by_name': self.user.username
                }
            )

    # WebSocket message handlers
    async def new_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'message': event['message']
        }))

    async def typing_indicator(self, event):
        await self.send(text_data=json.dumps({
            'type': 'typing_indicator',
            'conversation_id': event['conversation_id'],
            'user_id': event['user_id'],
            'username': event['username'],
            'is_typing': event['is_typing']
        }))

    async def message_read_receipt(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message_read_receipt',
            'message_id': event['message_id'],
            'read_by': event['read_by'],
            'read_by_name': event['read_by_name']
        }))

    async def user_status(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_status',
            'user_id': event['user_id'],
            'status': event['status']
        }))

    async def incoming_call(self, event):
        """Handle incoming call notifications"""
        print(f"DEBUG: Received incoming_call event for user {self.user.id}: {event}")
        await self.send(text_data=json.dumps({
            'type': 'incoming_call',
            'call': event['call']
        }))
        print(f"DEBUG: Sent incoming_call message to WebSocket for user {self.user.id}")

    # Database operations
    @database_sync_to_async
    def save_message(self, conversation_id, content):
        try:
            conversation = Conversation.objects.get(
                id=conversation_id,
                participants=self.user
            )
            try:
                message = Message.objects.create(
                    conversation=conversation,
                    sender=self.user,
                    content=content,
                    message_type='text'
                )
                return message
            except OperationalError as e:
                logger.exception(f"Database error creating websocket message for user {self.user.id}: {e}")
                return None
        except Conversation.DoesNotExist:
            return None

    @database_sync_to_async
    def get_conversation_participants(self, conversation_id):
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            return list(conversation.participants.values_list('id', flat=True))
        except Conversation.DoesNotExist:
            return []

    @database_sync_to_async
    def mark_message_read(self, message_id):
        try:
            from .message_models import MessageRead
            message = Message.objects.get(id=message_id)
            MessageRead.objects.get_or_create(message=message, user=self.user)
            return True
        except Message.DoesNotExist:
            return False

    @database_sync_to_async
    def get_message_sender(self, message_id):
        try:
            message = Message.objects.get(id=message_id)
            return message.sender.id
        except Message.DoesNotExist:
            return None


class CallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            await self.close()
            return
        
        # Support both string call_id and integer call_id from URL
        call_id_param = self.scope['url_route']['kwargs'].get('call_id')
        
        # Handle string call_id (from new implementation)
        if isinstance(call_id_param, str):
            self.call_id = call_id_param
        else:
            # Convert integer call_id to string for compatibility
            self.call_id = str(call_id_param)
            
        self.call_group_name = f"call_{self.call_id}"

        # Log incoming connection info for debugging
        try:
            logger.info("CallConsumer.connect: user=%s call_id=%s", getattr(self.user, 'id', None), self.call_id)
        except Exception:
            logger.exception("CallConsumer.connect: failed to log user/call_id")

        # Verify user is part of this call
        access = await self.verify_call_access()
        logger.info("CallConsumer.connect: verify_call_access=%s for user=%s call_id=%s", access, getattr(self.user, 'id', None), self.call_id)

        if not access:
            await self.close()
            return
        
        # Join call group
        await self.channel_layer.group_add(
            self.call_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send call state to connecting user
        await self.send_call_state()

    async def disconnect(self, close_code):
        if hasattr(self, 'call_group_name'):
            await self.channel_layer.group_discard(
                self.call_group_name,
                self.channel_name
            )
            
            # Send user left notification
            await self.channel_layer.group_send(
                self.call_group_name,
                {
                    'type': 'user_left_call',
                    'user_id': self.user.id,
                    'username': self.user.username
                }
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            signal_type = data.get('type')
            
            if signal_type == 'offer':
                await self.handle_offer(data)
            elif signal_type == 'answer':
                await self.handle_answer(data)
            elif signal_type == 'ice_candidate':
                await self.handle_ice_candidate(data)
            elif signal_type == 'call_status':
                await self.handle_call_status(data)
            elif signal_type == 'call_quality':
                await self.handle_call_quality(data)
            elif signal_type == 'join_call':
                await self.handle_join_call(data)
            elif signal_type == 'leave_call':
                await self.handle_leave_call(data)
            elif signal_type == 'toggle_media':
                await self.handle_toggle_media(data)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON'
            }))

    async def handle_offer(self, data):
        # Forward offer to other participants
        await self.channel_layer.group_send(
            self.call_group_name,
            {
                'type': 'webrtc_offer',
                'offer': data.get('offer'),
                'sender_id': self.user.id,
                'sender_name': self.user.username,
                'call_type': data.get('call_type', 'audio')
            }
        )
        
        # Update call status to ringing
        await self.update_call_status('ringing')

    async def handle_answer(self, data):
        # Forward answer to caller
        await self.channel_layer.group_send(
            self.call_group_name,
            {
                'type': 'webrtc_answer',
                'answer': data.get('answer'),
                'sender_id': self.user.id,
                'sender_name': self.user.username
            }
        )

    async def handle_ice_candidate(self, data):
        # Forward ICE candidate to other participants
        await self.channel_layer.group_send(
            self.call_group_name,
            {
                'type': 'webrtc_ice_candidate',
                'candidate': data.get('candidate'),
                'sender_id': self.user.id
            }
        )

    async def handle_call_status(self, data):
        status = data.get('status')
        
        if status in ['answered', 'ended', 'declined', 'missed']:
            await self.update_call_status(status)
            
        # Broadcast status to all participants
        await self.channel_layer.group_send(
            self.call_group_name,
            {
                'type': 'call_status_update',
                'status': status,
                'user_id': self.user.id,
                'username': self.user.username,
                'timestamp': data.get('timestamp')
            }
        )
        
        # Send FCM notification for important status changes
        if status in ['missed', 'declined']:
            self.send_fcm_notification(status)

    async def handle_call_quality(self, data):
        """Handle call quality updates"""
        quality_data = {
            'connection_quality': data.get('connection_quality', 'unknown'),
            'network_info': data.get('network_info', {}),
            'sender_id': self.user.id
        }
        
        # Broadcast quality info to other participants
        await self.channel_layer.group_send(
            self.call_group_name,
            {
                'type': 'call_quality_update',
                **quality_data
            }
        )
        
        # Update call record with quality metrics
        await self.update_call_quality(quality_data)

    async def handle_join_call(self, data):
        """Handle user joining an active call"""
        # Broadcast user joined to other participants
        await self.channel_layer.group_send(
            self.call_group_name,
            {
                'type': 'user_joined_call',
                'user_id': self.user.id,
                'username': self.user.username,
                'call_type': data.get('call_type', 'audio')
            }
        )
        
        # Update call participants list if this is a group call
        await self.update_call_participants()

    async def handle_leave_call(self, data):
        """Handle user leaving the call"""
        # Broadcast user left to other participants
        await self.channel_layer.group_send(
            self.call_group_name,
            {
                'type': 'user_left_call',
                'user_id': self.user.id,
                'username': self.user.username,
                'reason': data.get('reason', 'normal')
            }
        )
        
        # Update call status if all users left
        await self.check_call_termination()

    async def handle_toggle_media(self, data):
        """Handle media toggle (mute/unmute, camera on/off)"""
        await self.channel_layer.group_send(
            self.call_group_name,
            {
                'type': 'media_toggle',
                'user_id': self.user.id,
                'media_type': data.get('media_type'),  # 'audio' or 'video'
                'enabled': data.get('enabled'),
                'username': self.user.username
            }
        )

    # WebSocket message handlers
    async def webrtc_offer(self, event):
        if event['sender_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'offer',
                'offer': event['offer'],
                'sender_id': event['sender_id'],
                'sender_name': event['sender_name'],
                'call_type': event.get('call_type', 'audio')
            }))

    async def webrtc_answer(self, event):
        if event['sender_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'answer',
                'answer': event['answer'],
                'sender_id': event['sender_id'],
                'sender_name': event['sender_name']
            }))

    async def webrtc_ice_candidate(self, event):
        if event['sender_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'ice_candidate',
                'candidate': event['candidate'],
                'sender_id': event['sender_id']
            }))

    async def call_status_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'call_status',
            'status': event['status'],
            'user_id': event['user_id'],
            'username': event['username'],
            'timestamp': event.get('timestamp')
        }))
        
    async def call_quality_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'call_quality',
            'connection_quality': event['connection_quality'],
            'network_info': event['network_info'],
            'sender_id': event['sender_id']
        }))
        
    async def user_joined_call(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user_id': event['user_id'],
            'username': event['username'],
            'call_type': event.get('call_type', 'audio')
        }))
        
    async def user_left_call(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user_id': event['user_id'],
            'username': event['username'],
            'reason': event.get('reason', 'normal')
        }))
        
    async def media_toggle(self, event):
        await self.send(text_data=json.dumps({
            'type': 'media_toggle',
            'user_id': event['user_id'],
            'media_type': event['media_type'],
            'enabled': event['enabled'],
            'username': event['username']
        }))

    # Call notification handlers for API-triggered events
    async def call_notification(self, event):
        """Handle call notifications from API"""
        await self.send(text_data=json.dumps({
            'type': 'incoming_call',
            'call_id': event['call_id'],
            'caller_name': event['caller_name'],
            'caller_id': event['caller_id'],
            'call_type': event['call_type'],
            'action': event['action']
        }))
        
    async def call_answered(self, event):
        """Handle call answered notifications"""
        await self.send(text_data=json.dumps({
            'type': 'call_answered',
            'call_id': event['call_id'],
            'callee_name': event['callee_name'],
            'callee_id': event['callee_id']
        }))
        
    async def call_rejected(self, event):
        """Handle call rejected notifications"""
        await self.send(text_data=json.dumps({
            'type': 'call_rejected',
            'call_id': event['call_id'],
            'rejected_by': event['rejected_by']
        }))
        
    async def call_ended(self, event):
        """Handle call ended notifications"""
        await self.send(text_data=json.dumps({
            'type': 'call_ended',
            'call_id': event['call_id'],
            'duration': event['duration'],
            'ended_by': event['ended_by']
        }))

    # Database operations
    @database_sync_to_async
    def verify_call_access(self):
        logger.info(f"DEBUG: Looking for call_id={self.call_id} for user={self.user.id}")
        try:
            # First try to find by call_id (string format)
            call = Call.objects.get(call_id=self.call_id)
            logger.info(f"DEBUG: Found call by call_id: {call.id}, caller={call.caller_id}, receiver={call.receiver_id}")
        except Call.DoesNotExist:
            logger.info(f"DEBUG: Call not found by call_id, trying numeric id")
            try:
                # If not found, try to find by numeric id
                call = Call.objects.get(id=int(self.call_id))
                logger.info(f"DEBUG: Found call by id: {call.id}, caller={call.caller_id}, receiver={call.receiver_id}")
            except (Call.DoesNotExist, ValueError) as e:
                logger.info(f"DEBUG: Call not found by id either: {e}")
                return False
    
        # Check if user is caller, receiver, or participant
        has_access = (call.caller == self.user or call.receiver == self.user or
                     (call.participants and self.user.id in call.participants))
        logger.info(f"DEBUG: Access check result: {has_access}")
        return has_access

    @database_sync_to_async
    def update_call_status(self, status):
        try:
            # First try to find by call_id (string format)
            call = Call.objects.get(call_id=self.call_id)
        except Call.DoesNotExist:
            try:
                # If not found, try to find by numeric id
                call = Call.objects.get(id=int(self.call_id))
            except (Call.DoesNotExist, ValueError):
                return False
        # ... rest of method
        call.status = status
        from django.utils import timezone
        if status == 'answered' and not call.answered_at:
            call.answered_at = timezone.now()
        elif status in ['ended', 'declined', 'rejected'] and not call.ended_at:
            call.ended_at = timezone.now()
            if status in ['answered', 'ended'] and call.answered_at:
                call.duration = (timezone.now() - call.answered_at).total_seconds()
        call.save()
        return True
            
    @database_sync_to_async
    def update_call_quality(self, quality_data):
        try:
            call = Call.objects.get(call_id=self.call_id)
            call.connection_quality = quality_data.get('connection_quality', 'unknown')
            call.network_info = quality_data.get('network_info', {})
            call.save()
            return True
        except Call.DoesNotExist:
            return False
            
    @database_sync_to_async
    def update_call_participants(self):
        try:
            call = Call.objects.get(call_id=self.call_id)
            if call.participants:
                if self.user.id not in call.participants:
                    call.participants.append(self.user.id)
                    call.save()
            return True
        except Call.DoesNotExist:
            return False
            
    @database_sync_to_async
    def check_call_termination(self):
        try:
            call = Call.objects.get(call_id=self.call_id)
            # If this was a group call, check if all users left
            if call.participants and len(call.participants) > 1:
                # For group calls, don't auto-terminate
                return True
            # For individual calls, check if both parties have left
            from django.utils import timezone
            call.ended_at = timezone.now()
            call.status = 'ended'
            if call.answered_at:
                call.duration = (timezone.now() - call.answered_at).total_seconds()
            call.save()
            return True
        except Call.DoesNotExist:
            return False
    
    async def send_call_state(self):
        """Send current call state to connecting user"""
        call_data = await self.get_call_data()
        if call_data:
            await self.send(text_data=json.dumps({
                'type': 'call_state',
                'call': call_data
            }))
    
    @database_sync_to_async
    def get_call_data(self):
        try:
            # First try to find by call_id (string format)
            call = Call.objects.get(call_id=self.call_id)
        except Call.DoesNotExist:
            try:
                # If not found, try to find by numeric id
                call = Call.objects.get(id=int(self.call_id))
            except (Call.DoesNotExist, ValueError):
                return None
        # ... rest of method
        return {
            'call_id': call.call_id,
            'call_type': call.call_type,
            'status': call.status,
            'started_at': call.started_at.isoformat(),
            'answered_at': call.answered_at.isoformat() if call.answered_at else None,
            'caller': {
                'id': call.caller.id,
                'name': f"{call.caller.first_name} {call.caller.last_name}".strip() or call.caller.username
            },
            'callee': {
                'id': call.receiver.id,
                'name': f"{call.receiver.first_name} {call.receiver.last_name}".strip() or call.receiver.username
            } if call.receiver else None,
            'participants': call.participants
        }
    
    @database_sync_to_async
    def send_fcm_notification(self, status):
        """Send FCM notification for missed calls, etc."""
        try:
            call = Call.objects.get(call_id=self.call_id)
            from .fcm_service import fcm_service

            # Determine who should receive the notification
            if status == 'missed' and call.caller == self.user:
                # Caller's call was missed - notify callee
                target_user = call.receiver
            elif status == 'declined' and call.receiver == self.user:
                # Callee declined - notify caller
                target_user = call.caller
            else:
                return  # No notification needed

            # Try to get FCM token
            try:
                vendor_profile = VendorProfile.objects.get(user=target_user)
                if vendor_profile.fcm_token:
                    fcm_service.send_call_notification(
                        token=vendor_profile.fcm_token,
                        call_data={
                            'call_id': self.call_id,
                            'status': status,
                            'from_user': f"{self.user.first_name} {self.user.last_name}".strip(),
                            'action': 'call_missed'
                        }
                    )
            except VendorProfile.DoesNotExist:
                pass  # Customer doesn't have vendor profile

        except Call.DoesNotExist:
            pass


class UserConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            await self.close()
            return

        self.user_group_name = f"user_{self.user.id}"

        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )

    async def incoming_call(self, event):
        await self.send(text_data=json.dumps({
            'type': 'incoming_call',
            'call': event['call']
        }))


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            await self.close()
            return

        # Check if user is a vendor or customer
        is_vendor = await self.is_vendor_user()

        if is_vendor:
            self.user_group_name = f"vendor_notifications_{self.user.id}"
        else:
            self.user_group_name = f"customer_notifications_{self.user.id}"

        # Join notification group
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )

        await self.accept()

        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to notification service',
            'user_type': 'vendor' if is_vendor else 'customer'
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'authenticate':
                # Handle authentication if needed
                pass
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong'
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON'
            }))

    # Notification handlers
    async def order_notification(self, event):
        """Handle order notifications"""
        is_vendor = await self.is_vendor_user()
        action_url = '/vendor/orders' if is_vendor else '/orders'
        
        await self.send(text_data=json.dumps({
            'type': 'order_notification',
            'notification': {
                'id': event.get('notification_id'),
                'type': 'order',
                'title': event.get('title', 'Order Update'),
                'message': event.get('message'),
                'data': event.get('data', {}),
                'action_url': event.get('action_url', action_url)
            }
        }))

    async def payment_notification(self, event):
        """Handle payment notifications"""
        is_vendor = await self.is_vendor_user()
        action_url = '/vendor/wallet' if is_vendor else '/orders'
        
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': {
                'id': event.get('notification_id'),
                'type': 'payment',
                'title': event.get('title', 'Payment Update'),
                'message': event.get('message'),
                'data': event.get('data', {}),
                'action_url': event.get('action_url', action_url)
            }
        }))

    async def system_notification(self, event):
        """Handle system notifications"""
        is_vendor = await self.is_vendor_user()
        default_action_url = '/vendor/settings' if is_vendor else '/profile'
        
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': {
                'id': event.get('notification_id'),
                'type': 'system',
                'title': event.get('title', 'System Notification'),
                'message': event.get('message'),
                'data': event.get('data', {}),
                'action_url': event.get('action_url', default_action_url)
            }
        }))

    # Database operations
    @database_sync_to_async
    def is_vendor_user(self):
        """Check if the user is a vendor"""
        try:
            VendorProfile.objects.get(user=self.user)
            return True
        except VendorProfile.DoesNotExist:
            return False


# Utility function to send notifications to vendors
def send_vendor_notification(vendor_user_id, notification_type, title, message, data=None, action_url=None):
    """Send notification to a specific vendor"""
    import time
    from asgiref.sync import async_to_sync
    
    channel_layer = get_channel_layer()
    
    # Use time.time() instead of asyncio event loop time
    timestamp = int(time.time())
    
    async_to_sync(channel_layer.group_send)(
        f"vendor_notifications_{vendor_user_id}",
        {
            'type': f'{notification_type}_notification',
            'notification_id': f"{notification_type}_{vendor_user_id}_{timestamp}",
            'title': title,
            'message': message,
            'data': data or {},
            'action_url': action_url
        }
    )

# Utility function to send notifications to customers
def send_customer_notification(customer_user_id, notification_type, title, message, data=None, action_url=None):
    """Send notification to a specific customer"""
    import time
    from asgiref.sync import async_to_sync
    
    channel_layer = get_channel_layer()
    
    # Use time.time() instead of asyncio event loop time
    timestamp = int(time.time())
    
    async_to_sync(channel_layer.group_send)(
        f"customer_notifications_{customer_user_id}",
        {
            'type': f'{notification_type}_notification',
            'notification_id': f"{notification_type}_{customer_user_id}_{timestamp}",
            'title': title,
            'message': message,
            'data': data or {},
            'action_url': action_url
        }
    )