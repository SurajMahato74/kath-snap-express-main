from rest_framework import serializers
from .message_models import Conversation, Message, MessageRead, Call
from .serializers import UserSerializer

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    is_read = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = ['id', 'sender', 'message_type', 'content', 'file_url', 'file_name', 
                 'thumbnail_url', 'file_size', 'image_width', 'image_height',
                 'status', 'is_pinned', 'created_at', 'is_read']
        read_only_fields = ['id', 'sender', 'created_at']
    
    def get_is_read(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return MessageRead.objects.filter(message=obj, user=request.user).exists()
        return False

class ConversationSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    last_message = MessageSerializer(read_only=True)
    unread_count = serializers.SerializerMethodField()
    other_participant = serializers.SerializerMethodField()
    
    class Meta:
        model = Conversation
        fields = ['id', 'participants', 'last_message', 'unread_count', 'other_participant', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.messages.exclude(
                read_by__user=request.user
            ).exclude(sender=request.user).count()
        return 0
    
    def get_other_participant(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None

        current_user = request.user
        other_participants = obj.participants.exclude(id=current_user.id)

        if not other_participants.exists():
            return None

        # Handle 1-on-1 chats directly (most common)
        if other_participants.count() == 1:
            return UserSerializer(other_participants.first()).data

        # For group/multi-participant chats: filter out system/admin users first
        # Adjust 'admin', 'ezeyway', 'superadmin' based on your actual user_type values
        preferred_participants = other_participants.exclude(
            user_type__in=['admin', 'ezeyway', 'superadmin']
        )

        if preferred_participants.exists():
            other_participants = preferred_participants

        # Role-based priority
        if current_user.user_type == 'vendor':
            # Vendor: always prefer a real customer
            customers = other_participants.filter(user_type='customer')
            if customers.exists():
                return UserSerializer(customers.first()).data

        elif current_user.user_type == 'customer':
            # Customer: prefer the vendor they're talking to
            vendors = other_participants.filter(user_type='vendor')
            if vendors.exists():
                return UserSerializer(vendors.first()).data

        # Safe fallback: first remaining participant (never None)
        return UserSerializer(other_participants.first()).data
    
class CallSerializer(serializers.ModelSerializer):
    caller = UserSerializer(read_only=True)
    receiver = UserSerializer(read_only=True)
    
    class Meta:
        model = Call
        fields = ['id', 'caller', 'receiver', 'call_type', 'status', 'started_at', 
                 'answered_at', 'ended_at', 'duration']
        read_only_fields = ['id', 'caller', 'receiver', 'started_at', 'answered_at', 'ended_at', 'duration']

class SendMessageSerializer(serializers.Serializer):
    conversation_id = serializers.IntegerField(required=False)
    recipient_id = serializers.IntegerField(required=False)
    message_type = serializers.ChoiceField(choices=Message.MESSAGE_TYPES, default='text')
    content = serializers.CharField(required=False, allow_blank=True)
    file = serializers.FileField(required=False)
    
    def validate(self, attrs):
        if not attrs.get('conversation_id') and not attrs.get('recipient_id'):
            raise serializers.ValidationError("Either conversation_id or recipient_id is required")
        
        if attrs.get('message_type') == 'text' and not attrs.get('content'):
            raise serializers.ValidationError("Content is required for text messages")
        
        if attrs.get('message_type') in ['image', 'file'] and not attrs.get('file'):
            raise serializers.ValidationError("File is required for image/file messages")
        
        return attrs

class InitiateCallSerializer(serializers.Serializer):
    recipient_id = serializers.IntegerField()
    call_type = serializers.ChoiceField(choices=Call.CALL_TYPE, default='audio')