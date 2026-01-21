from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_call_api(request, call_id):
    """Accept an incoming call"""
    try:
        from .message_models import Call
        
        call = Call.objects.get(call_id=call_id)
        
        # Verify user can accept this call
        if call.receiver != request.user:
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        
        # Update call status
        call.status = 'answered'
        call.answered_at = timezone.now()
        call.save()
        
        # Notify caller via WebSocket/FCM
        from .websocket_fallback import send_call_with_fallback
        
        notification_data = {
            'type': 'call_accepted',
            'call_id': call_id,
            'accepter_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
            'accepter_id': str(request.user.id)
        }
        
        send_call_with_fallback(call.caller.id, notification_data)
        
        return Response({
            'success': True,
            'message': 'Call accepted',
            'call_id': call_id,
            'status': 'answered'
        })
        
    except Call.DoesNotExist:
        return Response({'error': 'Call not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Accept call error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_call_api(request, call_id):
    """Reject an incoming call"""
    try:
        from .message_models import Call
        
        call = Call.objects.get(call_id=call_id)
        
        # Verify user can reject this call
        if call.receiver != request.user:
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        
        # Update call status
        call.status = 'rejected'
        call.ended_at = timezone.now()
        call.duration = 0
        call.save()
        
        # Notify caller via WebSocket/FCM
        from .websocket_fallback import send_call_with_fallback
        
        notification_data = {
            'type': 'call_rejected',
            'call_id': call_id,
            'rejecter_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
            'rejecter_id': str(request.user.id)
        }
        
        send_call_with_fallback(call.caller.id, notification_data)
        
        return Response({
            'success': True,
            'message': 'Call rejected',
            'call_id': call_id,
            'status': 'rejected'
        })
        
    except Call.DoesNotExist:
        return Response({'error': 'Call not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Reject call error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def end_call_api(request, call_id):
    """End an active call"""
    try:
        from .message_models import Call
        
        call = Call.objects.get(call_id=call_id)
        
        # Verify user is part of this call
        if request.user not in [call.caller, call.receiver]:
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
        
        # Calculate duration
        if call.answered_at:
            duration = (timezone.now() - call.answered_at).total_seconds()
        else:
            duration = 0
        
        # Update call status
        call.status = 'ended'
        call.ended_at = timezone.now()
        call.duration = duration
        call.save()
        
        # Notify other party
        other_user = call.receiver if call.caller == request.user else call.caller
        from .websocket_fallback import send_call_with_fallback
        
        notification_data = {
            'type': 'call_ended',
            'call_id': call_id,
            'duration': duration,
            'ended_by': str(request.user.id)
        }
        
        send_call_with_fallback(other_user.id, notification_data)
        
        return Response({
            'success': True,
            'message': 'Call ended',
            'call_id': call_id,
            'duration': duration,
            'status': 'ended'
        })
        
    except Call.DoesNotExist:
        return Response({'error': 'Call not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"End call error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)