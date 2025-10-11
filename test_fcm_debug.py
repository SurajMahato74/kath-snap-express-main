#!/usr/bin/env python3
"""
FCM Debug Script - Test if notifications are working
Run this from backend/ezeyway directory
"""

import os
import sys
import django
from django.conf import settings

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend', 'ezeyway'))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ezeyway.settings')
django.setup()

from accounts.models import VendorProfile
from accounts.fcm_service import fcm_service

def test_fcm_setup():
    print("🔍 FCM Debug Test Started")
    print("=" * 50)
    
    # 1. Check if vendors have FCM tokens
    print("1. Checking vendor FCM tokens...")
    vendors = VendorProfile.objects.exclude(fcm_token__isnull=True).exclude(fcm_token='')
    
    if vendors.exists():
        print(f"✅ Found {vendors.count()} vendors with FCM tokens:")
        for vendor in vendors:
            token_preview = vendor.fcm_token[:20] + "..." if vendor.fcm_token else "None"
            print(f"   - {vendor.business_name}: {token_preview}")
    else:
        print("❌ No vendors found with FCM tokens!")
        print("   This means:")
        print("   - App is not registering FCM tokens")
        print("   - Or vendors haven't logged in yet")
        return False
    
    # 2. Test sending notification to first vendor
    print("\n2. Testing FCM notification...")
    test_vendor = vendors.first()
    
    if test_vendor and test_vendor.fcm_token:
        print(f"📱 Sending test notification to: {test_vendor.business_name}")
        
        success = fcm_service.send_order_notification(
            fcm_token=test_vendor.fcm_token,
            order_data={
                'orderId': 999,
                'orderNumber': 'TEST-999',
                'amount': '500'
            }
        )
        
        if success:
            print("✅ Test notification sent successfully!")
            print("   Check your mobile device for notification")
            print("   If app is closed, it should auto-open when tapped")
        else:
            print("❌ Failed to send test notification")
            print("   Check Firebase configuration and service account file")
    
    print("\n" + "=" * 50)
    print("🎯 Debug Summary:")
    print(f"   - Vendors with tokens: {vendors.count()}")
    print(f"   - Test notification: {'✅ Sent' if success else '❌ Failed'}")
    
    return True

def check_firebase_config():
    print("\n3. Checking Firebase configuration...")
    
    # Check service account file
    service_account_path = 'c:/Users/suraj/OneDrive/Desktop/BRANDWAVE/kath-snap-express-main/ezeyway-2f869-firebase-adminsdk-fbsvc-d8638b05a4.json'
    
    if os.path.exists(service_account_path):
        print("✅ Firebase service account file found")
    else:
        print("❌ Firebase service account file NOT found")
        print(f"   Expected path: {service_account_path}")
    
    # Check if Firebase is initialized
    try:
        import firebase_admin
        apps = firebase_admin._apps
        if apps:
            print("✅ Firebase Admin SDK is initialized")
        else:
            print("❌ Firebase Admin SDK not initialized")
    except Exception as e:
        print(f"❌ Firebase error: {e}")

if __name__ == "__main__":
    try:
        check_firebase_config()
        test_fcm_setup()
        
        print("\n🚀 Next Steps:")
        print("1. If no FCM tokens found:")
        print("   - Install app on device and login as vendor")
        print("   - Check browser console for FCM token logs")
        print("2. If notification failed:")
        print("   - Check Firebase project settings")
        print("   - Verify service account file path")
        print("3. If notification sent but app doesn't open:")
        print("   - Install @capacitor-community/fcm plugin")
        print("   - Check Android manifest configuration")
        
    except Exception as e:
        print(f"❌ Error running debug script: {e}")
        import traceback
        traceback.print_exc()