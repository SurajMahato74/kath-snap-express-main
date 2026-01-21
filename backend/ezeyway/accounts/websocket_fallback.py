from .fcm_service import fcm_service
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

logger = logging.getLogger(__name__)

def send_call_with_fallback(user_id, call_data):
    """Try WebSocket first, fallback to FCM if it fails"""
    channel_layer = get_channel_layer()
    
    # For testing: Force FCM by skipping WebSocket
    force_fcm = call_data.get('force_fcm', False)
    
    if not force_fcm:
        try:
            # Try WebSocket first - send in frontend-compatible format
            async_to_sync(channel_layer.group_send)(
                f"user_{user_id}",
                {
                    'type': 'call_notification',
                    'call': {
                        'id': call_data.get('call_id'),
                        'caller_id': int(call_data.get('caller_id', 0)),
                        'caller_name': call_data.get('caller_name', ''),
                        'recipient_id': user_id,
                        'recipient_name': '',  # Will be filled by frontend
                        'call_type': call_data.get('call_type', 'audio'),
                        'status': 'ringing'
                    }
                }
            )
            logger.info(f"✅ WebSocket call sent to user {user_id}")
            
            # If WebSocket succeeds but we want to test FCM too, continue to FCM
            if not call_data.get('test_fcm_too', False):
                return True
            else:
                logger.info(f"🧪 WebSocket sent, now testing FCM too...")
        except Exception as e:
            logger.warning(f"❌ WebSocket failed for user {user_id}: {e}")
    else:
        logger.info(f"🧪 Forcing FCM test, skipping WebSocket for user {user_id}")
        
    # Fallback to FCM - send in frontend-compatible format
    try:
        from .models import CustomUser, VendorProfile
        user = CustomUser.objects.get(id=user_id)
        
        # Try to get FCM token from VendorProfile first
        fcm_token = None
        try:
            vendor_profile = VendorProfile.objects.get(user=user)
            fcm_token = vendor_profile.fcm_token
        except VendorProfile.DoesNotExist:
            # Check if user has direct FCM token
            fcm_token = getattr(user, 'fcm_token', None)
        
        if fcm_token:
            # Send FCM with frontend-compatible data structure
            fcm_data = {
                'type': 'incoming_call',
                'call_id': call_data.get('call_id'),
                'caller_name': call_data.get('caller_name'),
                'caller_id': call_data.get('caller_id'),
                'call_type': call_data.get('call_type', 'audio')
            }
            
            logger.info(f"🚀 Attempting FCM send to user {user_id}...")
            success = fcm_service.send_call_notification(fcm_token, fcm_data)
            if success:
                logger.info(f"✅ FCM notification sent to user {user_id}")
                return True
            else:
                logger.error(f"❌ FCM send failed for user {user_id}")
        else:
            logger.warning(f"❌ No FCM token for user {user_id}")
            
    except Exception as fcm_error:
        logger.error(f"❌ FCM fallback error for user {user_id}: {fcm_error}")
    
    return False