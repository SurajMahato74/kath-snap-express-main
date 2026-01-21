#!/usr/bin/env python
"""
Simple Call Test - Send FCM notifications to test devices
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
from accounts.fcm_service import fcm_service

def test_fcm_calls():
    """Send FCM call notifications directly"""
    print("📞 Sending Call Notifications...")
    
    profiles = VendorProfile.objects.filter(
        fcm_token__isnull=False,
        fcm_token__gt=''
    ).select_related('user')
    
    if not profiles:
        print("❌ No devices found")
        return
    
    print(f"📱 Testing {len(profiles)} devices")
    
    test_call_id = f"test_{uuid.uuid4().hex[:8]}"
    
    for profile in profiles:
        call_data = {
            'call_id': test_call_id,
            'caller_name': 'Test Call',
            'caller_id': '999',
            'call_type': 'audio'
        }
        
        success = fcm_service.send_call_notification(profile.fcm_token, call_data)
        status = "✅" if success else "❌"
        print(f"{status} {profile.user.username}")
    
    print("\n🎉 Done! Check your phones.")

if __name__ == "__main__":
    test_fcm_calls()