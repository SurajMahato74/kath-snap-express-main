#!/usr/bin/env python3
"""
FCM Call Notification Test Script
Tests background call notifications that auto-open app
"""
import os
import sys
import django
import json

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ezeyway.settings')
django.setup()

from accounts.models import CustomUser, VendorProfile
from accounts.fcm_service import fcm_service

def test_fcm_initialization():
    """Test if FCM service is properly initialized"""
    print("=== Testing FCM Initialization ===")
    
    try:
        import firebase_admin
        if firebase_admin._apps:
            print("✅ Firebase Admin SDK initialized")
            return True
        else:
            print("❌ Firebase Admin SDK not initialized")
            print("Check firebase service account file path")
            return False
    except Exception as e:
        print(f"❌ FCM initialization error: {e}")
        return False

def get_test_fcm_token():
    """Get FCM token from a vendor for testing"""
    print("\n=== Getting Test FCM Token ===")
    
    try:
        vendor_profile = VendorProfile.objects.filter(fcm_token__isnull=False).first()
        if vendor_profile and vendor_profile.fcm_token:
            print(f"✅ Found FCM token for vendor: {vendor_profile.user.username}")
            print(f"Token: {vendor_profile.fcm_token[:30]}...")
            return vendor_profile.fcm_token, vendor_profile.user
        else:
            print("❌ No vendor with FCM token found")
            print("Register a vendor in the app first to get FCM token")
            return None, None
    except Exception as e:
        print(f"❌ Error getting FCM token: {e}")
        return None, None

def test_call_notification(fcm_token, caller_name="Test Caller"):
    """Test call notification that should wake up app"""
    print(f"\n=== Testing Call Notification ===")
    
    try:
        from firebase_admin import messaging
        
        # Call notification with high priority and auto-open flags
        message = messaging.Message(
            token=fcm_token,
            notification=messaging.Notification(
                title=f"📞 Incoming Call",
                body=f"{caller_name} is calling you..."
            ),
            data={
                'type': 'incoming_call',
                'call_id': 'test_call_123',
                'caller_id': '79',
                'caller_name': caller_name,
                'call_type': 'audio',
                'action': 'show_call_screen',
                'autoOpen': 'true',
                'forceOpen': 'true',
                'wakeUp': 'true',
                'click_action': 'FLUTTER_NOTIFICATION_CLICK'
            },
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    channel_id='call_notifications',
                    priority='max',  # Highest priority
                    sound='default',
                    default_vibrate_timings=True,
                    default_light_settings=True,
                    sticky=True,
                    visibility='public',
                    click_action='FLUTTER_NOTIFICATION_CLICK',
                    tag='incoming_call'  # Replace previous call notifications
                )
            ),
            # iOS configuration for VoIP-like behavior
            apns=messaging.APNSConfig(
                headers={
                    'apns-priority': '10',  # Immediate delivery
                    'apns-push-type': 'alert'
                },
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        alert=messaging.ApsAlert(
                            title=f"📞 Incoming Call",
                            body=f"{caller_name} is calling you..."
                        ),
                        sound='default',
                        badge=1,
                        category='CALL_CATEGORY'
                    )
                )
            )
        )
        
        response = messaging.send(message)
        print(f"✅ Call notification sent successfully: {response}")
        print("📱 Check your phone - app should open with call screen!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send call notification: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_missed_call_notification(fcm_token, caller_name="Test Caller"):
    """Test missed call notification"""
    print(f"\n=== Testing Missed Call Notification ===")
    
    try:
        from firebase_admin import messaging
        
        message = messaging.Message(
            token=fcm_token,
            notification=messaging.Notification(
                title=f"📞 Missed Call",
                body=f"You missed a call from {caller_name}"
            ),
            data={
                'type': 'missed_call',
                'call_id': 'test_call_123',
                'caller_id': '79',
                'caller_name': caller_name,
                'action': 'show_call_history',
                'click_action': 'FLUTTER_NOTIFICATION_CLICK'
            },
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    channel_id='call_notifications',
                    priority='high',
                    sound='default',
                    click_action='FLUTTER_NOTIFICATION_CLICK'
                )
            )
        )
        
        response = messaging.send(message)
        print(f"✅ Missed call notification sent: {response}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send missed call notification: {e}")
        return False

def create_fcm_test_endpoint():
    """Create a test endpoint for manual FCM testing"""
    print(f"\n=== Creating FCM Test Endpoint ===")
    
    endpoint_code = '''
# Add this to your Django views for manual testing

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from accounts.fcm_service import fcm_service
import json

@csrf_exempt
def test_fcm_call_notification(request):
    """Manual FCM test endpoint"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            fcm_token = data.get('fcm_token')
            caller_name = data.get('caller_name', 'Test Caller')
            
            if not fcm_token:
                return JsonResponse({'error': 'fcm_token required'}, status=400)
            
            # Send call notification
            success = fcm_service.send_call_notification(fcm_token, {
                'call_id': 'test_123',
                'caller_name': caller_name,
                'caller_id': '79',
                'call_type': 'audio'
            })
            
            if success:
                return JsonResponse({'message': 'Call notification sent!'})
            else:
                return JsonResponse({'error': 'Failed to send notification'}, status=500)
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'POST method required'}, status=405)

# Add to urls.py:
# path('test-fcm-call/', test_fcm_call_notification, name='test_fcm_call'),
'''
    
    print("✅ Test endpoint code generated")
    print("Add this to your views.py and urls.py for manual testing")
    
    # Save to file
    with open('fcm_test_endpoint.py', 'w') as f:
        f.write(endpoint_code)
    print("✅ Saved to fcm_test_endpoint.py")

def test_curl_command(fcm_token):
    """Generate curl command for testing"""
    print(f"\n=== CURL Test Command ===")
    
    curl_cmd = f'''
# Test FCM call notification via curl:
curl -X POST https://ezeyway.com/api/test-fcm-call/ \\
  -H "Content-Type: application/json" \\
  -d '{{
    "fcm_token": "{fcm_token[:30]}...",
    "caller_name": "Test Caller"
  }}'
'''
    
    print(curl_cmd)
    return curl_cmd

def check_fcm_service_methods():
    """Check if FCM service has call notification method"""
    print(f"\n=== Checking FCM Service Methods ===")
    
    methods = dir(fcm_service)
    call_methods = [m for m in methods if 'call' in m.lower()]
    
    if call_methods:
        print(f"✅ Found call-related methods: {call_methods}")
    else:
        print("❌ No call-related methods found")
        print("Need to add send_call_notification method to FCMService")
        
    return bool(call_methods)

def add_call_notification_method():
    """Add call notification method to FCM service"""
    print(f"\n=== Adding Call Notification Method ===")
    
    method_code = '''
def send_call_notification(self, fcm_token, call_data):
    """Send HIGH PRIORITY call notification that wakes up app"""
    try:
        if not fcm_token:
            logger.warning("No FCM token provided for call")
            return False

        if not firebase_admin._apps:
            logger.error("Firebase not initialized")
            return False

        logger.info(f"Sending CALL notification to: {fcm_token[:20]}...")

        message = messaging.Message(
            token=fcm_token,
            notification=messaging.Notification(
                title='📞 Incoming Call',
                body=f"{call_data.get('caller_name', 'Someone')} is calling you..."
            ),
            data={
                'type': 'incoming_call',
                'call_id': call_data.get('call_id', ''),
                'caller_id': str(call_data.get('caller_id', '')),
                'caller_name': call_data.get('caller_name', ''),
                'call_type': call_data.get('call_type', 'audio'),
                'action': 'show_call_screen',
                'autoOpen': 'true',
                'forceOpen': 'true',
                'wakeUp': 'true',
                'click_action': 'FLUTTER_NOTIFICATION_CLICK'
            },
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    channel_id='call_notifications',
                    priority=AndroidNotificationPriority.MAX,
                    sound='default',
                    default_vibrate_timings=True,
                    default_light_settings=True,
                    sticky=True,
                    visibility=AndroidNotificationVisibility.PUBLIC,
                    click_action='FLUTTER_NOTIFICATION_CLICK',
                    tag='incoming_call'
                )
            )
        )

        response = messaging.send(message)
        logger.info(f"Call notification sent: {response}")
        return True

    except Exception as e:
        logger.error(f"Failed to send call notification: {e}")
        return False
'''
    
    print("✅ Call notification method code generated")
    print("Add this method to FCMService class in fcm_service.py")
    
    # Save to file
    with open('call_notification_method.py', 'w') as f:
        f.write(method_code)
    print("✅ Saved to call_notification_method.py")

def main():
    """Run all FCM tests"""
    print("🚀 Starting FCM Call Notification Tests")
    print("=" * 60)
    
    # Test 1: FCM initialization
    if not test_fcm_initialization():
        print("❌ FCM not initialized - fix Firebase setup first")
        return
    
    # Test 2: Get FCM token
    fcm_token, user = get_test_fcm_token()
    if not fcm_token:
        print("❌ No FCM token available - register a vendor first")
        return
    
    # Test 3: Check FCM service methods
    has_call_methods = check_fcm_service_methods()
    if not has_call_methods:
        add_call_notification_method()
    
    # Test 4: Send call notification
    print(f"\n🔥 SENDING CALL NOTIFICATION TO {user.username}")
    print("📱 CHECK YOUR PHONE NOW!")
    
    success = test_call_notification(fcm_token, "Test Caller")
    
    if success:
        print("\n✅ Call notification sent successfully!")
        print("📱 Your phone should show incoming call screen")
        print("🔔 App should auto-open even if locked")
    else:
        print("\n❌ Call notification failed")
    
    # Test 5: Send missed call notification
    test_missed_call_notification(fcm_token, "Test Caller")
    
    # Test 6: Generate test tools
    create_fcm_test_endpoint()
    test_curl_command(fcm_token)
    
    print("\n" + "=" * 60)
    print("📋 FCM Call Notification Test Complete")
    print("\n🎯 Next Steps:")
    print("1. Check your phone for notifications")
    print("2. Add call notification method to FCMService")
    print("3. Test with real call flow")
    print("4. Configure notification channels in app")

if __name__ == "__main__":
    main()