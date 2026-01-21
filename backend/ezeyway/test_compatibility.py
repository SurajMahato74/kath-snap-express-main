#!/usr/bin/env python
"""
Live Call Test - Send Real FCM Notifications to All Active Mobile Devices

This script sends test call notifications to all users with FCM tokens.
Run this on your server to test real mobile notifications.
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
from accounts.websocket_fallback import send_call_with_fallback

def send_test_calls_to_all_devices():
    """Send test call notifications to all devices with FCM tokens"""
    print("📱 LIVE CALL TEST - Sending to All Active Mobile Devices")
    print("=" * 60)
    
    # Get all users with FCM tokens
    users_with_tokens = []
    
    # Check vendor profiles for FCM tokens
    vendor_profiles = VendorProfile.objects.filter(
        fcm_token__isnull=False,
        fcm_token__gt=''
    ).select_related('user')
    
    for profile in vendor_profiles:
        users_with_tokens.append({
            'user': profile.user,
            'fcm_token': profile.fcm_token,
            'type': 'vendor'
        })
    
    print(f"📋 Found {len(users_with_tokens)} devices with FCM tokens")
    
    if not users_with_tokens:
        print("❌ No devices found with FCM tokens!")
        print("💡 Make sure your mobile app has registered FCM tokens")
        return
    
    # Generate test call data
    test_call_id = f"test_call_{uuid.uuid4().hex[:8]}"
    test_caller_name = "Test Server"
    test_caller_id = "999"
    
    print(f"\n🔥 Sending test call: {test_call_id}")
    print(f"📞 Caller: {test_caller_name}")
    print(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}")
    print("\n" + "-" * 40)
    
    successful_sends = 0
    failed_sends = 0
    
    for device in users_with_tokens:
        user = device['user']
        fcm_token = device['fcm_token']
        device_type = device['type']
        
        print(f"\n📱 Sending to: {user.username} ({device_type})")
        print(f"🔑 Token: {fcm_token[:20]}...")
        
        # Prepare call data with FCM testing flags
        call_data = {
            'call_id': test_call_id,
            'caller_name': test_caller_name,
            'caller_id': test_caller_id,
            'call_type': 'audio',
            'action': 'show_call_screen',
            'force_fcm': True,  # Force FCM for testing
            'test_fcm_too': True  # Test both WebSocket and FCM
        }
        
        try:
            # Use the fallback mechanism (tries WebSocket first, then FCM)
            success = send_call_with_fallback(user.id, call_data)
            
            if success:
                print(f"✅ SUCCESS: Call sent to {user.username}")
                successful_sends += 1
            else:
                print(f"❌ FAILED: Could not send to {user.username}")
                failed_sends += 1
                
        except Exception as e:
            print(f"❌ ERROR: {user.username} - {str(e)}")
            failed_sends += 1
    
    print("\n" + "=" * 60)
    print(f"📊 RESULTS:")
    print(f"✅ Successful: {successful_sends}")
    print(f"❌ Failed: {failed_sends}")
    print(f"📱 Total devices: {len(users_with_tokens)}")
    
    if successful_sends > 0:
        print("\n🎉 SUCCESS! Check your mobile devices now!")
        print("📱 You should see incoming call notifications")
        print("🔔 Even if the app is closed/minimized")
    else:
        print("\n⚠️ No notifications sent successfully")
        print("💡 Check Firebase configuration and FCM tokens")
    
    print("\n" + "=" * 60)

def test_single_device():
    """Test with a specific device (interactive mode)"""
    print("\n🎯 SINGLE DEVICE TEST")
    print("-" * 30)
    
    # List available devices
    vendor_profiles = VendorProfile.objects.filter(
        fcm_token__isnull=False,
        fcm_token__gt=''
    ).select_related('user')
    
    if not vendor_profiles:
        print("❌ No devices with FCM tokens found")
        return
    
    print("Available devices:")
    for i, profile in enumerate(vendor_profiles, 1):
        print(f"{i}. {profile.user.username} - {profile.business_name}")
    
    try:
        choice = input("\nEnter device number (or press Enter for all): ").strip()
        
        if choice:
            device_index = int(choice) - 1
            if 0 <= device_index < len(vendor_profiles):
                profile = vendor_profiles[device_index]
                print(f"\n📱 Testing with: {profile.user.username}")
                
                call_data = {
                    'call_id': f"single_test_{uuid.uuid4().hex[:8]}",
                    'caller_name': 'Single Test',
                    'caller_id': '888',
                    'call_type': 'video',
                    'action': 'show_call_screen'
                }
                
                success = send_call_with_fallback(profile.user.id, call_data)
                
                if success:
                    print(f"✅ Test call sent to {profile.user.username}!")
                else:
                    print(f"❌ Failed to send test call")
            else:
                print("❌ Invalid device number")
        else:
            send_test_calls_to_all_devices()
            
    except (ValueError, KeyboardInterrupt):
        print("\n👋 Test cancelled")

if __name__ == "__main__":
    print("🚀 LIVE CALL NOTIFICATION TESTER")
    print("=" * 60)
    print("This will send REAL call notifications to mobile devices!")
    print("Make sure your mobile app is ready to receive them.")
    print("\nOptions:")
    print("1. Send to ALL devices with FCM tokens")
    print("2. Send to a specific device")
    print("3. Exit")
    
    try:
        choice = input("\nChoose option (1-3): ").strip()
        
        if choice == '1':
            send_test_calls_to_all_devices()
        elif choice == '2':
            test_single_device()
        elif choice == '3':
            print("👋 Goodbye!")
        else:
            print("❌ Invalid choice")
            
    except KeyboardInterrupt:
        print("\n\n👋 Test cancelled by user")