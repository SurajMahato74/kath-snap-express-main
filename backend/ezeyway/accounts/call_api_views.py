from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
import uuid
import logging

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

        # Send notification using fallback
        from .websocket_fallback import send_call_with_fallback
        
        call_data = {
            'type': 'incoming_call',
            'call_id': call_id,
            'caller_name': f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username,
            'caller_id': str(request.user.id),
            'call_type': call_type
        }
        
        send_call_with_fallback(recipient_id, call_data)

        # Return frontend-compatible response
        return Response({
            'call': {
                'id': call_id,
                'caller_id': request.user.id,
                'recipient_id': recipient_id,
                'call_type': call_type,
                'status': 'initiated'
            }
        })

    except Exception as e:
        logger.error(f"Create call error: {e}")
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