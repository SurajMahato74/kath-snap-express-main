from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .fcm_service import fcm_service
from .models import VendorProfile
import json
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_fcm_call_notification(request):
    """Manual FCM call notification test endpoint"""
    try:
        data = request.data
        fcm_token = data.get('fcm_token')
        caller_name = data.get('caller_name', 'Test Caller')
        
        # If no token provided, try to get from current user
        if not fcm_token:
            try:
                vendor_profile = VendorProfile.objects.get(user=request.user)
                fcm_token = vendor_profile.fcm_token
            except VendorProfile.DoesNotExist:
                return Response({'error': 'No FCM token found for user'}, status=400)
        
        if not fcm_token:
            return Response({'error': 'fcm_token required'}, status=400)
        
        logger.info(f"Testing FCM call notification to token: {fcm_token[:20]}...")
        
        # Send call notification
        success = fcm_service.send_call_notification(
            fcm_token=fcm_token,
            call_data={
                'call_id': 'test_call_123',
                'caller_id': request.user.id,
                'caller_name': caller_name,
                'call_type': 'audio'
            }
        )
        
        if success:
            return Response({
                'message': 'Call notification sent successfully!',
                'token': fcm_token[:20] + '...',
                'caller_name': caller_name
            })
        else:
            return Response({'error': 'Failed to send notification'}, status=500)
            
    except Exception as e:
        logger.error(f"FCM test error: {e}")
        return Response({'error': str(e)}, status=500)

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_fcm_token(request):
    """Get FCM token for current user"""
    try:
        vendor_profile = VendorProfile.objects.get(user=request.user)
        if vendor_profile.fcm_token:
            return Response({
                'fcm_token': vendor_profile.fcm_token,
                'user': request.user.username,
                'token_preview': vendor_profile.fcm_token[:30] + '...'
            })
        else:
            return Response({'error': 'No FCM token registered'}, status=404)
    except VendorProfile.DoesNotExist:
        return Response({'error': 'User is not a vendor'}, status=404)

@csrf_exempt
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_fcm_token(request):
    """Update FCM token for current user"""
    try:
        fcm_token = request.data.get('fcm_token')
        if not fcm_token:
            return Response({'error': 'fcm_token required'}, status=400)
        
        vendor_profile, created = VendorProfile.objects.get_or_create(user=request.user)
        vendor_profile.fcm_token = fcm_token
        vendor_profile.save()
        
        return Response({
            'message': 'FCM token updated successfully',
            'token_preview': fcm_token[:30] + '...'
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)