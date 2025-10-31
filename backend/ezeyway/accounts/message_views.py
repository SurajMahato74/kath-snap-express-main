from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q, Prefetch
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from django.utils import timezone
import os
from .models import CustomUser
from .message_models import Conversation, Message, MessageRead, Call
from .message_serializers import (
    ConversationSerializer, MessageSerializer, CallSerializer,
    SendMessageSerializer, InitiateCallSerializer
)

class ConversationListView(generics.ListAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Conversation.objects.filter(
            participants=self.request.user
        ).prefetch_related(
            'participants',
            'messages'
        )

class ConversationDetailView(generics.RetrieveAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user)

class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        conversation_id = self.kwargs['conversation_id']
        conversation = get_object_or_404(
            Conversation.objects.filter(participants=self.request.user),
            id=conversation_id
        )
        
        # Mark messages as read
        unread_messages = Message.objects.filter(
            conversation=conversation
        ).exclude(sender=self.request.user).exclude(
            read_by__user=self.request.user
        )
        
        for message in unread_messages:
            MessageRead.objects.get_or_create(message=message, user=self.request.user)
        
        return Message.objects.filter(conversation=conversation).order_by('-created_at')

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def send_message_api(request):
    # Handle special case for superadmin recipient_type
    if request.data.get('recipient_type') == 'superadmin':
        # Find the superadmin user (ezeywaya)
        try:
            superadmin_user = CustomUser.objects.get(username='ezeywaya')
        except CustomUser.DoesNotExist:
            return Response({'error': 'Superadmin not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if conversation already exists
        conversation = Conversation.objects.filter(
            participants=request.user
        ).filter(participants=superadmin_user).first()

        if not conversation:
            conversation = Conversation.objects.create()
            conversation.participants.add(request.user, superadmin_user)

        # Create message
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            message_type='text',
            content=request.data.get('message', '')
        )

        # Mark as read by sender
        MessageRead.objects.create(message=message, user=request.user)

        # Update conversation timestamp
        conversation.save()

        return Response({
            'message': MessageSerializer(message, context={'request': request}).data,
            'conversation': ConversationSerializer(conversation, context={'request': request}).data
        }, status=status.HTTP_201_CREATED)

    # Original send_message_api logic
    serializer = SendMessageSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    # Get or create conversation
    if data.get('conversation_id'):
        conversation = get_object_or_404(
            Conversation.objects.filter(participants=request.user),
            id=data['conversation_id']
        )
    else:
        recipient = get_object_or_404(CustomUser, id=data['recipient_id'])
        
        # Check if conversation already exists
        conversation = Conversation.objects.filter(
            participants=request.user
        ).filter(participants=recipient).first()
        
        if not conversation:
            conversation = Conversation.objects.create()
            conversation.participants.add(request.user, recipient)
    
    # Handle file upload
    file_data = {}
    if data.get('file'):
        uploaded_file = data['file']
        
        if data['message_type'] == 'image':
            # Use image processor for images
            from .image_utils import ImageProcessor
            try:
                processed_data = ImageProcessor.process_message_image(
                    uploaded_file, conversation.id, request.user.id
                )
                file_data.update(processed_data)
            except ValueError as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            # Handle regular files
            file_extension = os.path.splitext(uploaded_file.name)[1]
            filename = f"messages/{conversation.id}_{request.user.id}_{uploaded_file.name}"
            file_path = default_storage.save(filename, uploaded_file)
            file_data.update({
                'file_url': file_path,
                'file_name': uploaded_file.name,
                'file_size': uploaded_file.size
            })
    
    # Create message
    message = Message.objects.create(
        conversation=conversation,
        sender=request.user,
        message_type=data['message_type'],
        content=data.get('content', ''),
        **file_data
    )
    
    # Mark as read by sender
    MessageRead.objects.create(message=message, user=request.user)
    
    # Update conversation timestamp
    conversation.save()
    
    return Response({
        'message': MessageSerializer(message, context={'request': request}).data,
        'conversation': ConversationSerializer(conversation, context={'request': request}).data
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_message_read_api(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    
    # Check if user is participant in conversation
    if not message.conversation.participants.filter(id=request.user.id).exists():
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    MessageRead.objects.get_or_create(message=message, user=request.user)
    
    return Response({'message': 'Message marked as read'})

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_pin_message_api(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    
    # Check if user is participant in conversation
    if not message.conversation.participants.filter(id=request.user.id).exists():
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    message.is_pinned = not message.is_pinned
    message.save()
    
    return Response({
        'message': 'Message pin toggled',
        'is_pinned': message.is_pinned
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_or_create_conversation_api(request, user_id):
    other_user = get_object_or_404(CustomUser, id=user_id)
    
    # Check if conversation already exists
    conversation = Conversation.objects.filter(
        participants=request.user
    ).filter(participants=other_user).first()
    
    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, other_user)
    
    return Response(ConversationSerializer(conversation, context={'request': request}).data)

# Call APIs
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def initiate_call_api(request):
    serializer = InitiateCallSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    recipient = get_object_or_404(CustomUser, id=serializer.validated_data['recipient_id'])
    
    # End any existing calls
    Call.objects.filter(
        Q(caller=request.user, receiver=recipient) | Q(caller=recipient, receiver=request.user),
        status__in=['initiated', 'ringing', 'answered']
    ).update(status='ended', ended_at=timezone.now())
    
    # Get or create conversation
    conversation = Conversation.objects.filter(
        participants=request.user
    ).filter(participants=recipient).first()
    
    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, recipient)
    
    # Create call record
    call = Call.objects.create(
        conversation=conversation,
        caller=request.user,
        receiver=recipient,
        call_type=serializer.validated_data['call_type'],
        status='ringing'
    )
    
    # Debug logging
    print(f"Call created: ID={call.id}, Caller={call.caller.id}, Receiver={call.receiver.id}, Status={call.status}")
    
    return Response({
        'call': CallSerializer(call).data,
        'conversation_id': conversation.id
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def answer_call_api(request, call_id):
    call = get_object_or_404(Call, id=call_id, receiver=request.user)
    
    if call.status != 'ringing':
        return Response({'error': 'Call is not in ringing state'}, status=status.HTTP_400_BAD_REQUEST)
    
    call.status = 'answered'
    call.answered_at = timezone.now()
    call.save()
    
    return Response(CallSerializer(call).data)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def end_call_api(request, call_id):
    call = get_object_or_404(
        Call.objects.filter(
            Q(caller=request.user) | Q(receiver=request.user)
        ),
        id=call_id
    )
    
    call.end_call()
    
    return Response(CallSerializer(call).data)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def decline_call_api(request, call_id):
    call = get_object_or_404(Call, id=call_id, receiver=request.user)
    
    if call.status not in ['initiated', 'ringing']:
        return Response({'error': 'Call cannot be declined'}, status=status.HTTP_400_BAD_REQUEST)
    
    call.status = 'declined'
    call.ended_at = timezone.now()
    call.save()
    
    return Response(CallSerializer(call).data)

class CallHistoryView(generics.ListAPIView):
    serializer_class = CallSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Call.objects.filter(
            Q(caller=self.request.user) | Q(receiver=self.request.user)
        ).order_by('-started_at')

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def incoming_calls_api(request):
    # Auto-hangup calls older than 50 seconds
    timeout_calls = Call.objects.filter(
        receiver=request.user,
        status__in=['initiated', 'ringing'],
        started_at__lt=timezone.now() - timezone.timedelta(seconds=50)
    )
    timeout_calls.update(status='missed', ended_at=timezone.now())
    
    calls = Call.objects.filter(
        receiver=request.user,
        status__in=['initiated', 'ringing']
    ).order_by('-started_at')
    
    # Debug logging
    print(f"User {request.user.id} checking incoming calls")
    print(f"Found {calls.count()} calls with status: {[c.status for c in calls]}")
    
    return Response(CallSerializer(calls, many=True).data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def message_image_api(request, message_id):
    """Serve message images with access control"""
    message = get_object_or_404(Message, id=message_id, message_type='image')
    
    # Check if user has access to this conversation
    if not message.conversation.participants.filter(id=request.user.id).exists():
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    # Return image URLs
    return Response({
        'image_url': message.file_url,
        'thumbnail_url': message.thumbnail_url,
        'file_name': message.file_name,
        'file_size': message.file_size,
        'dimensions': {
            'width': message.image_width,
            'height': message.image_height
        } if message.image_width and message.image_height else None
    })

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_support_conversation_api(request):
    """Create a conversation with superadmin for support"""
    try:
        superadmin_user = CustomUser.objects.get(username='ezeywaya')
    except CustomUser.DoesNotExist:
        return Response({'error': 'Support not available'}, status=status.HTTP_404_NOT_FOUND)

    # Check if conversation already exists
    conversation = Conversation.objects.filter(
        participants=request.user
    ).filter(participants=superadmin_user).first()

    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, superadmin_user)

    # If message is provided, create it
    message_content = request.data.get('message')
    if message_content:
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            message_type='text',
            content=message_content
        )
        # Mark as read by sender
        MessageRead.objects.create(message=message, user=request.user)
        # Update conversation timestamp
        conversation.save()

    return Response({
        'conversation_id': conversation.id,
        'message': 'Support conversation created' if not message_content else 'Message sent to support'
    }, status=status.HTTP_201_CREATED)