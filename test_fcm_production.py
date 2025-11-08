#!/usr/bin/env python3
"""
Production FCM Test Script
Tests FCM notifications in production environment
"""

import os
import sys
import django
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ezeyway.settings')
django.setup()

from backend.ezeyway.accounts.fcm_service import fcm_service
from backend.ezeyway.accounts.models import VendorProfile

def test_fcm_production():
    """Test FCM notifications in production"""
    print("🚀 Testing FCM in Production Environment")
    print("=" * 50)

    # Check Firebase initialization
    print("\n1. Checking Firebase initialization...")
    try:
        # Try to send a test notification to first vendor with FCM token
        vendors_with_tokens = VendorProfile.objects.filter(
            fcm_token__isnull=False,
            is_approved=True
        ).exclude(fcm_token='')

        if not vendors_with_tokens.exists():
            print("❌ No vendors with FCM tokens found")
            print("💡 Make sure vendors have logged into the mobile app recently")
            return

        test_vendor = vendors_with_tokens.first()
        print(f"✅ Found vendor with FCM token: {test_vendor.business_name}")
        print(f"📱 FCM Token: {test_vendor.fcm_token[:30]}...")

        # Test FCM notification
        print("\n2. Sending test FCM notification...")
        order_data = {
            'orderId': 'TEST-999',
            'orderNumber': 'TEST-999',
            'amount': '500.00'
        }

        success = fcm_service.send_order_notification(test_vendor.fcm_token, order_data)

        if success:
            print("✅ FCM notification sent successfully!")
            print("📱 Check the vendor's mobile device for notification")
            print("🔊 Notification should play sound and auto-open app when tapped")
        else:
            print("❌ FCM notification failed")
            print("🔍 Check server logs for detailed error information")

    except Exception as e:
        print(f"❌ FCM test failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 50)
    print("FCM Production Test Complete")

if __name__ == "__main__":
    test_fcm_production()