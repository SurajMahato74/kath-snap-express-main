#!/usr/bin/env python3
"""
Send Test FCM Notification
Run this to manually test if notifications work
"""

import os
import sys
import django

# Set up Django
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend', 'ezeyway'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ezeyway.settings')
django.setup()

from accounts.models import VendorProfile
from accounts.fcm_service import fcm_service

def send_test_notification():
    print("🚀 Sending Test Notification...")
    
    # Get vendor with FCM token
    vendor = VendorProfile.objects.exclude(fcm_token__isnull=True).exclude(fcm_token='').first()
    
    if not vendor:
        print("❌ No vendor found with FCM token")
        print("   Please login to the app first as a vendor")
        return
    
    print(f"📱 Sending to: {vendor.business_name}")
    print(f"🔑 Token: {vendor.fcm_token[:20]}...")
    
    # Send notification
    success = fcm_service.send_order_notification(
        fcm_token=vendor.fcm_token,
        order_data={
            'orderId': 12345,
            'orderNumber': 'TEST-12345',
            'amount': '750'
        }
    )
    
    if success:
        print("✅ Notification sent successfully!")
        print("\n🎯 What should happen:")
        print("1. If app is open: Notification appears in app")
        print("2. If app is closed: Notification appears in system tray")
        print("3. Tap notification: App should auto-open to vendor dashboard")
        print("4. Order modal should show with order details")
    else:
        print("❌ Failed to send notification")
        print("   Check Firebase configuration")

if __name__ == "__main__":
    send_test_notification()