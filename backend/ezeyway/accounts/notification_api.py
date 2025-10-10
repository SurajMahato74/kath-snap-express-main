from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from .message_models import Conversation
import json

@csrf_exempt
@login_required
def check_notifications(request):
    """Check for new message notifications"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Get user's conversations
        conversations = Conversation.objects.filter(participants=request.user)
        notifications = []
        
        for conv in conversations:
            # Check cache for new messages
            cache_key = f'new_message_{conv.id}'
            cached_message = cache.get(cache_key)
            
            if cached_message and cached_message['sender'] != request.user.username:
                notifications.append({
                    'conversation_id': conv.id,
                    'sender': cached_message['sender'],
                    'content': cached_message['content'],
                    'timestamp': cached_message['timestamp'],
                    'type': 'message'
                })
                # Clear cache after reading
                cache.delete(cache_key)
        
        return JsonResponse({
            'notifications': notifications,
            'count': len(notifications)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)