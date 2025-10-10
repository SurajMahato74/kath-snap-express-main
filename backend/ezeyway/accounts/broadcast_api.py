from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
import json
import time

@csrf_exempt
def broadcast_message(request):
    """Broadcast message notification across domains"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message_data = {
                'sender': data.get('sender'),
                'content': data.get('content'),
                'conversation_id': data.get('conversation_id'),
                'timestamp': time.time(),
                'type': 'message'
            }
            
            # Store in cache for other clients to pick up
            cache_key = f'broadcast_message_{message_data["conversation_id"]}_{message_data["timestamp"]}'
            cache.set(cache_key, message_data, 30)  # 30 seconds
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    elif request.method == 'GET':
        # Get recent broadcasts
        conversation_id = request.GET.get('conversation_id')
        since = float(request.GET.get('since', 0))
        
        try:
            # Get all cached messages for this conversation
            messages = []
            cache_keys = cache.keys(f'broadcast_message_{conversation_id}_*') if conversation_id else []
            
            for key in cache_keys:
                message_data = cache.get(key)
                if message_data and message_data['timestamp'] > since:
                    messages.append(message_data)
            
            return JsonResponse({'messages': messages})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)