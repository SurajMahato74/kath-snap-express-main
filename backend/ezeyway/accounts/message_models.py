from django.db import models
from django.utils import timezone
from .models import CustomUser

class Conversation(models.Model):
    participants = models.ManyToManyField(CustomUser, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        participant_names = ", ".join([user.username for user in self.participants.all()[:2]])
        return f"Conversation: {participant_names}"
    
    @property
    def last_message(self):
        return self.messages.first()

class Message(models.Model):
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
        ('system', 'System'),
    ]
    
    STATUS_CHOICES = [
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
    ]
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    content = models.TextField(blank=True, null=True)
    file_url = models.CharField(max_length=500, blank=True, null=True)
    file_name = models.CharField(max_length=255, blank=True, null=True)
    # Image-specific fields
    thumbnail_url = models.CharField(max_length=500, blank=True, null=True)
    file_size = models.IntegerField(blank=True, null=True)
    image_width = models.IntegerField(blank=True, null=True)
    image_height = models.IntegerField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='sent')
    is_pinned = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.sender.username}: {self.content[:50] if self.content else self.file_name}"

class MessageRead(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='read_by')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('message', 'user')
    
    def __str__(self):
        return f"{self.user.username} read {self.message.id}"

class Call(models.Model):
    CALL_STATUS = [
        ('initiated', 'Initiated'),
        ('ringing', 'Ringing'),
        ('answered', 'Answered'),
        ('ended', 'Ended'),
        ('missed', 'Missed'),
        ('declined', 'Declined'),
        ('rejected', 'Rejected'),
    ]
    
    CALL_TYPE = [
        ('audio', 'Audio'),
        ('video', 'Video'),
    ]
    
    QUALITY_CHOICES = [
        ('poor', 'Poor'),
        ('fair', 'Fair'),
        ('good', 'Good'),
        ('excellent', 'Excellent'),
    ]
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='calls', blank=True, null=True)
    caller = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='initiated_calls')
    receiver = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_calls')
    call_type = models.CharField(max_length=10, choices=CALL_TYPE, default='audio')
    status = models.CharField(max_length=10, choices=CALL_STATUS, default='initiated')
    call_id = models.CharField(max_length=100, unique=True, help_text='Unique ID for WebSocket routing')
    
    # Timing fields
    started_at = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(blank=True, null=True)
    ended_at = models.DateTimeField(blank=True, null=True)
    duration = models.IntegerField(default=0, help_text='Duration in seconds')
    
    # Quality metrics
    connection_quality = models.CharField(max_length=10, choices=QUALITY_CHOICES, blank=True, null=True)
    caller_network_info = models.JSONField(blank=True, null=True, help_text='Network info from caller')
    receiver_network_info = models.JSONField(blank=True, null=True, help_text='Network info from receiver')
    
    # Additional metadata
    call_metadata = models.JSONField(blank=True, null=True, help_text='Additional call metadata')
    participants = models.JSONField(default=list, help_text='List of user IDs participating in the call')

    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.caller.username} -> {self.receiver.username} ({self.status})"
    
    def generate_call_id(self):
        """Generate unique call ID for WebSocket routing"""
        import time
        if not self.call_id:
            self.call_id = f"call_{self.caller.id}_{self.receiver.id}_{int(time.time())}"
        return self.call_id
    
    def save(self, *args, **kwargs):
        # Generate call_id if not exists
        if not self.call_id:
            import time
            self.call_id = f"call_{self.caller.id}_{self.receiver.id}_{int(time.time())}"

        # Initialize participants if empty
        if not self.participants:
            self.participants = [self.caller.id, self.receiver.id]

        super().save(*args, **kwargs)
    
    def end_call(self):
        if self.status in ['answered', 'ringing']:
            self.status = 'ended'
            self.ended_at = timezone.now()
            if self.answered_at:
                self.duration = int((self.ended_at - self.answered_at).total_seconds())
            self.save()
    
    @property
    def is_active(self):
        return self.status in ['initiated', 'ringing', 'answered']
    
    @property
    def can_be_answered(self):
        return self.status in ['initiated', 'ringing'] and not self.ended_at