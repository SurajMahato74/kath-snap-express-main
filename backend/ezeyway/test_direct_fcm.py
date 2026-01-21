#!/usr/bin/env python
"""
Direct FCM Test - Test FCM notifications directly without WebSocket

This script sends FCM notifications directly to test if Firebase is working.
"""

import os
import sys
import django
import uuid
from datetime import datetime

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ezeyway.settings')
django.setup()

from accounts.models import CustomUser, VendorProfile
from accounts.fcm_service import fcm_service

def test_direct_fcm():
    """Test FCM notifications directly"""
    print("🔥 DIRECT FCM TEST - Testing Firebase Notifications")
    print("=" * 60)
    
    # Get all users with FCM tokens
    vendor_profiles = VendorProfile.objects.filter(
        fcm_token__isnull=False,
        fcm_token__gt=''
    ).select_related('user')
    
    if not vendor_profiles:
        print("❌ No devices found with FCM tokens!")
        return
    
    print(f"📋 Found {len(vendor_profiles)} devices with FCM tokens")
    
    test_call_id = f"direct_fcm_test_{uuid.uuid4().hex[:8]}"
    
    for profile in vendor_profiles:
        user = profile.user
        fcm_token = profile.fcm_token
        
        print(f"\n📱 Testing FCM for: {user.username}")
        print(f"🔑 Token: {fcm_token[:30]}...")
        
        # Test call data
        call_data = {
            'type': 'incoming_call',
            'call_id': test_call_id,
            'caller_name': 'Direct FCM Test',
            'caller_id': '777',
            'call_type': 'audio'
        }
        
        try:
            print("🚀 Sending FCM notification...")
            success = fcm_service.send_call_notification(fcm_token, call_data)
            
            if success:
                print(f"✅ FCM sent successfully to {user.username}")
                print("📱 Check your mobile device now!")
            else:
                print(f"❌ FCM failed for {user.username}")
                
        except Exception as e:
            print(f"❌ Error sending FCM to {user.username}: {e}")
    
    print("\n" + "=" * 60)
    print("🔔 If FCM is working, you should see notifications on your mobile devices")
    print("📱 The notifications should appear even if the app is closed")

def test_fcm_token_validity():
    """Test if FCM tokens are valid"""
    print("\n🔍 TESTING FCM TOKEN VALIDITY")
    print("-" * 40)
    
    vendor_profiles = VendorProfile.objects.filter(
        fcm_token__isnull=False,
        fcm_token__gt=''
    ).select_related('user')
    
    for profile in vendor_profiles:
        token = profile.fcm_token
        print(f"\n👤 {profile.user.username}:")
        print(f"📱 Token length: {len(token)}")
        print(f"🔑 Token starts with: {token[:20]}...")
        print(f"⏰ Last updated: {profile.fcm_updated_at}")
        
        # Basic token validation
        if len(token) < 100:
            print("⚠️  Token seems too short")
        elif not token.startswith(('f', 'c', 'd', 'e')):
            print("⚠️  Token format might be invalid")
        else:
            print("✅ Token format looks valid")

if __name__ == "__main__":
    print("🧪 FCM DIRECT TESTING TOOL")
    print("=" * 60)
    
    # Test token validity first
    test_fcm_token_validity()
    
    # Then test direct FCM
    test_direct_fcm()
    
    print("\n💡 TROUBLESHOOTING:")
    print("1. Check Firebase console for delivery status")
    print("2. Verify FCM tokens are recent (not expired)")
    print("3. Ensure mobile app has FCM properly configured")
    print("4. Check if notifications are enabled in device settings")