#!/usr/bin/env python3

import os
import sys
import django

# Add the Django project to the path
sys.path.append('c:/Users/suraj/OneDrive/Desktop/BRANDWAVE/kath-snap-express-main/backend/ezeyway')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ezeyway.settings')
django.setup()

from accounts.firebase_init import send_data_only_message

def test_real_order_notification():
    """Test sending a real order notification with sound"""
    
    # Your FCM token (replace with actual token)
    fcm_token = "c5EatI4yQPW6p7KjHDsSXu:APA91bF0XRUWOs786de6AOPap9z5I5VB8k6nKOcHGzoWiGr6fzd7aQ8j3Xxxnbc7QvSY07C_Ykl6mBQZo_BvfNMo0zRM7WPb4RXmS4Bx_rRT5utf2b6QI8o"
    
    # Test order data
    order_data = {
        "autoOpen": "true",
        "orderId": "999",
        "orderNumber": "TEST-REAL-ORDER",
        "amount": "750",
        "action": "autoOpenOrder",
        "forceOpen": "true"
    }
    
    print("🧪 Testing REAL ORDER notification with sound...")
    print(f"📱 FCM Token: {fcm_token[:30]}...")
    print(f"📦 Order Data: {order_data}")
    
    # Send the notification
    success = send_data_only_message(fcm_token, order_data)
    
    if success:
        print("✅ NOTIFICATION SENT! App should auto-open now!")
        print("📱 Check your phone - the app should open automatically")
    else:
        print("❌ Failed to send notification")

if __name__ == "__main__":
    test_real_order_notification()