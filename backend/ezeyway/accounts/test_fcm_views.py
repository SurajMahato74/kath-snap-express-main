from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import FCMToken
from .firebase_init import initialize_firebase, send_fcm_message, send_data_only_message
import json
import os

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_fcm_notification(request):
    """Test FCM notification endpoint"""
    try:
        # Initialize Firebase
        firebase_initialized = initialize_firebase()
        
        # Get user's FCM tokens
        fcm_tokens = FCMToken.objects.filter(user=request.user, is_active=True)
        
        # Debug info
        debug_info = {
            'firebase_initialized': firebase_initialized,
            'vendor_found': True,
            'fcm_token_exists': fcm_tokens.exists(),
            'fcm_token_count': fcm_tokens.count(),
            'service_account_paths': {}
        }
        
        # Check service account file paths
        service_account_paths = [
            '/home/ezeywayc/kath-snap-express-main/ezeyway-2f869-firebase-adminsdk-fbsvc-d8638b05a4.json',
            '/home/ezeywayc/ezeyway-2f869-firebase-adminsdk-fbsvc-d8638b05a4.json',
            './ezeyway-2f869-firebase-adminsdk-fbsvc-d8638b05a4.json'
        ]
        
        for path in service_account_paths:
            debug_info['service_account_paths'][path] = os.path.exists(path)
        
        if fcm_tokens.exists():
            debug_info['fcm_token_preview'] = fcm_tokens.first().token[:20] + '...'
        
        # Get test data from request
        test_data = request.data
        debug_info['test_data'] = {
            'title': test_data.get('title', 'Test Notification'),
            'message': test_data.get('message', 'Test message'),
            'order_id': test_data.get('orderId', 999),
            'order_number': test_data.get('orderNumber', 'TEST-999'),
            'amount': test_data.get('amount', '500')
        }
        
        if not firebase_initialized:
            return Response({
                'error': 'Firebase not initialized - check server logs',
                'debug': debug_info
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        if not fcm_tokens.exists():
            return Response({
                'error': 'No FCM tokens found for user',
                'debug': debug_info
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Send test notifications
        success_count = 0
        for fcm_token in fcm_tokens:
            # Send regular notification
            success1 = send_fcm_message(
                token=fcm_token.token,
                title=debug_info['test_data']['title'],
                body=debug_info['test_data']['message'],
                data={
                    'orderId': str(debug_info['test_data']['order_id']),
                    'orderNumber': debug_info['test_data']['order_number'],
                    'amount': debug_info['test_data']['amount'],
                    'type': 'test_notification'
                }
            )
            
            # Send auto-open data message
            success2 = send_data_only_message(
                token=fcm_token.token,
                data={
                    'autoOpen': 'true',
                    'orderId': str(debug_info['test_data']['order_id']),
                    'orderNumber': debug_info['test_data']['order_number'],
                    'amount': debug_info['test_data']['amount'],
                    'action': 'autoOpenOrder',
                    'forceOpen': 'true',
                    'type': 'auto_open_test'
                }
            )
            
            if success1 or success2:
                success_count += 1
        
        debug_info['send_result'] = success_count > 0
        
        if success_count > 0:
            return Response({
                'message': f'Test notifications sent successfully to {success_count} tokens',
                'debug': debug_info
            })
        else:
            return Response({
                'error': 'Failed to send notification - check server logs',
                'debug': debug_info
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        return Response({
            'error': f'Server error: {str(e)}',
            'debug': debug_info if 'debug_info' in locals() else {}
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_auto_open_notification(request):
    """Test auto-open FCM notification"""
    try:
        from .fcm_utils import send_auto_open_fcm_message, send_background_trigger
        
        # Send auto-open FCM message
        success = send_auto_open_fcm_message(
            user=request.user,
            order_id=999,
            order_number='TEST-AUTO-OPEN',
            amount='500'
        )
        
        # Also send background trigger
        send_background_trigger(
            user=request.user,
            order_data={
                'order_id': 999,
                'order_number': 'TEST-AUTO-OPEN',
                'amount': '500'
            }
        )
        
        return Response({
            'message': 'Auto-open test notification sent',
            'success': success,
            'user_id': request.user.id,
            'username': request.user.username
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to send test notification: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
