#!/usr/bin/env python
"""
Call System Test - Production Ready

Quick test to verify call notifications are working.
Run: python test_calls.py
"""

import os
import sys
import django
import uuid

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ezeyway.settings')
django.setup()

from accounts.models import VendorProfile
from accounts.websocket_fallback import send_call_with_fallback

def test_call_notifications():
    """Send test call notifications to all active devices"""
    print("📞 Testing Call Notifications...")
    
    # Get users with FCM tokens
    profiles = VendorProfile.objects.filter(
        fcm_token__isnull=False,
        fcm_token__gt=''
    ).select_related('user')
    
    if not profiles:
        print("❌ No devices with FCM tokens found")
        return
    
    print(f"📱 Found {len(profiles)} devices")
    
    # Send test call to each device
    test_call_id = f"test_{uuid.uuid4().hex[:8]}"
    
    for profile in profiles:
        call_data = {
            'call_id': test_call_id,
            'caller_name': 'Test Call',
            'caller_id': '999',
            'call_type': 'audio',
            'force_fcm': True  # Force FCM for testing
        }
        
        success = send_call_with_fallback(profile.user.id, call_data)
        status = "✅" if success else "❌"
        print(f"{status} {profile.user.username}")
    
    print("\n🎉 Test complete! Check your mobile devices.")

if __name__ == "__main__":
    test_call_notifications()