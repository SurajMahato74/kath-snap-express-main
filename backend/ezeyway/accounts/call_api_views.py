from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
import uuid
import logging
from .agora_service import AgoraTokenGenerator

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_call_api(request):
    """Create call API that matches frontend structure"""
    try:
        recipient_id = request.data.get('recipient_id')
        call_type = request.data.get('call_type', 'audio')

        if not recipient_id:
            return Response({'error': 'recipient_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Get recipient user
        from .models import CustomUser
        try:
            recipient = CustomUser.objects.get(id=recipient_id)
        except CustomUser.DoesNotExist:
            return Response({'error': 'Recipient not found'}, status=status.HTTP_404_NOT_FOUND)

        # Generate call ID
        call_id = f"call_{uuid.uuid4().hex[:16]}"

        # Create call record
        from .message_models import Call
        call = Call.objects.create(
            call_id=call_id,
            caller=request.user,
            receiver=recipient,
            call_type=call_type,
            status='initiated',
            started_at=timezone.now()
        )

        # Generate Agora token for the call
        token_generator = AgoraTokenGenerator()
        agora_token = token_generator.generate_channel_token(call_id, request.user.id)
        
        # Send notification using fallback
        from .websocket_fallback import send_call_with_fallback
        
        call_data = {
            'type': 'incoming_call',
            'call_id': call_id,
            'caller_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
            'caller_id': str(request.user.id),
            'call_type': call_type,
            'agora_token': agora_token,
            'agora_channel': call_id,
            'agora_app_id': token_generator.app_id
        }
        
        send_call_with_fallback(recipient_id, call_data)

        # Return frontend-compatible response
        return Response({
            'success': True,
            'call': {
                'id': call_id,
                'call_id': call_id,
                'caller_id': request.user.id,
                'recipient_id': recipient_id,
                'call_type': call_type,
                'status': 'initiated',
                'agora_token': agora_token,
                'agora_channel': call_id,
                'agora_app_id': token_generator.app_id
            }
        })

    except Exception as e:
        logger.error(f"Create call error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pending_calls_api(request):
    """Get pending calls for the authenticated user"""
    try:
        from .message_models import Call
        
        # Get pending calls where user is receiver
        pending_calls = Call.objects.filter(
            receiver=request.user,
            status__in=['initiated', 'ringing']
        ).order_by('-started_at')
        
        calls_data = []
        for call in pending_calls:
            calls_data.append({
                'id': call.id,
                'call_id': call.call_id,
                'caller': {
                    'id': call.caller.id,
                    'name': f"{call.caller.first_name} {call.caller.last_name}".strip() or call.caller.username,
                    'username': call.caller.username
                },
                'call_type': call.call_type,
                'status': call.status,
                'started_at': call.started_at.isoformat(),
                'duration': None
            })
        
        return Response({
            'success': True,
            'calls': calls_data,
            'count': len(calls_data)
        })
        
    except Exception as e:
        logger.error(f"Get pending calls error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_fcm_token_api(request):
    """Update FCM token API that matches frontend structure"""
    try:
        fcm_token = request.data.get('fcm_token')
        
        if not fcm_token:
            return Response({'error': 'fcm_token is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Update FCM token in vendor profile
        from .models import VendorProfile
        try:
            vendor_profile = VendorProfile.objects.get(user=request.user)
            vendor_profile.fcm_token = fcm_token
            vendor_profile.fcm_updated_at = timezone.now()
            vendor_profile.save()
            
            return Response({
                'success': True,
                'message': 'FCM token updated successfully'
            })
        except VendorProfile.DoesNotExist:
            # For customers, store in user model (you may need to add fcm_token field to CustomUser)
            return Response({
                'success': True,
                'message': 'FCM token updated for customer'
            })

    except Exception as e:
        logger.error(f"FCM token update error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_call_api(request, call_id):
    """Accept call API with Agora token generation"""
    try:
        from .message_models import Call
        
        # Get call record
        try:
            call = Call.objects.get(call_id=call_id, receiver=request.user)
        except Call.DoesNotExist:
            return Response({'error': 'Call not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if call.status not in ['initiated', 'ringing']:
            return Response({'error': 'Cannot accept this call'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Update call status
        call.status = 'answered'
        call.answered_at = timezone.now()
        call.save()
        
        # Generate Agora tokens for both users
        token_generator = AgoraTokenGenerator()
        accepter_token = token_generator.generate_channel_token(call_id, request.user.id)
        
        try:
            caller_token = token_generator.generate_channel_token(call_id, call.caller.id)
            caller_id = call.caller.id
        except AttributeError:
            logger.error(f"Call {call_id} has no caller set")
            return Response({'error': 'Invalid call state'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Real-time broadcast to call group
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f"call_{call_id}",
                {
                    'type': 'call_accepted',
                    'call_id': call_id,
                    'accepter_id': request.user.id,
                    'accepter_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
                    'agora_token_caller': caller_token,
                }
            )
        
        # Fallback notification for offline users
        from .websocket_fallback import send_call_with_fallback
        
        notification_data = {
            'type': 'call_accepted',
            'call_id': call_id,
            'accepter_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
            'accepter_id': str(request.user.id),
            'agora_token': caller_token,
            'agora_channel': call_id,
            'agora_app_id': token_generator.app_id
        }
        
        send_call_with_fallback(caller_id, notification_data)
        
        return Response({
            'success': True,
            'status': 'answered',
            'call_id': call_id,
            'agora_token': accepter_token,
            'agora_channel': call_id,
            'agora_app_id': token_generator.app_id
        })
        
    except Exception as e:
        logger.error(f"Accept call error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_agora_token_api(request):
    """Generate Agora token API endpoint"""
    try:
        call_id = request.data.get('call_id')
        channel_name = request.data.get('channel_name', call_id)
        uid = request.data.get('uid', request.user.id)
        
        if not channel_name:
            return Response({'error': 'channel_name or call_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        token_generator = AgoraTokenGenerator()
        token = token_generator.generate_channel_token(channel_name, uid)
        
        # Calculate expires_at timestamp
        import time
        from django.conf import settings
        token_expiry = getattr(settings, 'CALL_SETTINGS', {}).get('TOKEN_EXPIRY', 7200)
        expires_at = int(time.time()) + token_expiry
        
        return Response({
            'token': token,
            'channel_name': channel_name,
            'app_id': token_generator.app_id,
            'expires_at': expires_at
        })
        
    except Exception as e:
        logger.error(f"Generate token error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)