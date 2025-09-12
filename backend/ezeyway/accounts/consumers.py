import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .message_models import Conversation, Message, Call
from .models import VendorProfile
from channels.layers import get_channel_layer

User = get_user_model()

class MessageConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            await self.close()
            return
        
        self.user_group_name = f"user_{self.user.id}"
        
        # Join user group
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
        
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

    # Database operations
    @database_sync_to_async
    def save_message(self, conversation_id, content):
        try:
            conversation = Conversation.objects.get(
                id=conversation_id,
                participants=self.user
            )
            message = Message.objects.create(
                conversation=conversation,
                sender=self.user,
                content=content,
                message_type='text'
            )
            return message
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
        
        self.call_id = self.scope['url_route']['kwargs']['call_id']
        self.call_group_name = f"call_{self.call_id}"
        
        # Verify user is part of this call
        if not await self.verify_call_access():
            await self.close()
            return
        
        # Join call group
        await self.channel_layer.group_add(
            self.call_group_name,
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'call_group_name'):
            await self.channel_layer.group_discard(
                self.call_group_name,
                self.channel_name
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
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON'
            }))

    async def handle_offer(self, data):
        # Forward offer to other participant
        await self.channel_layer.group_send(
            self.call_group_name,
            {
                'type': 'webrtc_offer',
                'offer': data.get('offer'),
                'sender_id': self.user.id
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
                'sender_id': self.user.id
            }
        )

    async def handle_ice_candidate(self, data):
        # Forward ICE candidate to other participant
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
        if status in ['ended', 'declined']:
            await self.update_call_status(status)
            
        # Broadcast status to all participants
        await self.channel_layer.group_send(
            self.call_group_name,
            {
                'type': 'call_status_update',
                'status': status,
                'user_id': self.user.id
            }
        )

    # WebSocket message handlers
    async def webrtc_offer(self, event):
        if event['sender_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'offer',
                'offer': event['offer'],
                'sender_id': event['sender_id']
            }))

    async def webrtc_answer(self, event):
        if event['sender_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'answer',
                'answer': event['answer'],
                'sender_id': event['sender_id']
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
            'user_id': event['user_id']
        }))

    # Database operations
    @database_sync_to_async
    def verify_call_access(self):
        try:
            call = Call.objects.get(id=self.call_id)
            return call.caller == self.user or call.receiver == self.user
        except Call.DoesNotExist:
            return False

    @database_sync_to_async
    def update_call_status(self, status):
        try:
            call = Call.objects.get(id=self.call_id)
            call.status = status
            if status == 'answered':
                from django.utils import timezone
                call.answered_at = timezone.now()
            elif status in ['ended', 'declined']:
                call.end_call()
            call.save()
            return True
        except Call.DoesNotExist:
            return False


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