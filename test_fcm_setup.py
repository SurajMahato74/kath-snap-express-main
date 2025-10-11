#!/usr/bin/env python3
"""
FCM Push Notification Test Script
Tests the complete FCM setup for ezeyway app
"""

import os
import sys
import django
import json
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent / 'backend' / 'ezeyway'
sys.path.insert(0, str(backend_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ezeyway.settings')
django.setup()

from accounts.fcm_service import fcm_service
from accounts.models import VendorProfile

def test_fcm_setup():
    print("🔥 Testing FCM Push Notification Setup")
    print("=" * 50)
    
    # Test 1: Check Firebase Admin SDK initialization
    print("\n1. Testing Firebase Admin SDK initialization...")
    try:
        fcm_service.initialize_firebase()
        print("✅ Firebase Admin SDK initialized successfully")
    except Exception as e:
        print(f"❌ Firebase initialization failed: {e}")
        return False
    
    # Test 2: Check if vendors have FCM tokens
    print("\n2. Checking vendor FCM tokens...")
    vendors_with_tokens = VendorProfile.objects.exclude(fcm_token__isnull=True).exclude(fcm_token='')
    print(f"📱 Found {vendors_with_tokens.count()} vendors with FCM tokens")
    
    for vendor in vendors_with_tokens[:3]:  # Show first 3
        print(f"   - {vendor.business_name}: {vendor.fcm_token[:20]}...")
    
    # Test 3: Send test notification
    if vendors_with_tokens.exists():
        print("\n3. Sending test notification...")
        test_vendor = vendors_with_tokens.first()
        
        test_order_data = {
            'orderId': 999,
            'orderNumber': 'TEST-ORDER-001',
            'amount': 150.00
        }
        
        try:
            success = fcm_service.send_order_notification(
                fcm_token=test_vendor.fcm_token,
                order_data=test_order_data
            )
            
            if success:
                print(f"✅ Test notification sent to {test_vendor.business_name}")
                print(f"📱 Check your mobile app for the notification!")
            else:
                print("❌ Failed to send test notification")
        except Exception as e:
            print(f"❌ Error sending notification: {e}")
    else:
        print("⚠️ No vendors with FCM tokens found - cannot send test notification")
    
    # Test 4: Check Android configuration
    print("\n4. Checking Android configuration...")
    android_manifest = Path(__file__).parent / 'kath-snap-express-main' / 'android' / 'app' / 'src' / 'main' / 'AndroidManifest.xml'
    
    if android_manifest.exists():
        with open(android_manifest, 'r') as f:
            manifest_content = f.read()
            
        if 'FCMService' in manifest_content:
            print("✅ FCM service configured in AndroidManifest.xml")
        else:
            print("❌ FCM service NOT found in AndroidManifest.xml")
            
        if 'WAKE_LOCK' in manifest_content:
            print("✅ WAKE_LOCK permission configured")
        else:
            print("❌ WAKE_LOCK permission missing")
    else:
        print("❌ AndroidManifest.xml not found")
    
    # Test 5: Check google-services.json
    google_services = Path(__file__).parent / 'kath-snap-express-main' / 'android' / 'app' / 'google-services.json'
    
    if google_services.exists():
        with open(google_services, 'r') as f:
            config = json.load(f)
            
        project_id = config.get('project_info', {}).get('project_id')
        if project_id == 'ezeyway-2f869':
            print("✅ google-services.json configured correctly")
        else:
            print(f"❌ Wrong project ID in google-services.json: {project_id}")
    else:
        print("❌ google-services.json not found")
    
    print("\n" + "=" * 50)
    print("🎯 FCM Setup Test Complete!")
    print("\n📋 Next Steps:")
    print("1. Build and install the app on your device")
    print("2. Login as a vendor to register FCM token")
    print("3. Create a test order to trigger notification")
    print("4. Check if notification opens the app when closed")
    
    return True

if __name__ == '__main__':
    test_fcm_setup()