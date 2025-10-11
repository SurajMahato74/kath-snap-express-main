#!/usr/bin/env python3

import os
import sys
import django

# Add the Django project to the path
sys.path.append('c:/Users/suraj/OneDrive/Desktop/BRANDWAVE/kath-snap-express-main/backend/ezeyway')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ezeyway.settings')
django.setup()

from accounts.firebase_init import send_data_only_message

def test_direct_fcm():
    """Test sending FCM directly to known token"""
    
    # Your known FCM token
    fcm_token = "c5EatI4yQPW6p7KjHDsSXu:APA91bF0XRUWOs786de6AOPap9z5I5VB8k6nKOcHGzoWiGr6fzd7aQ8j3Xxxnbc7QvSY07C_Ykl6mBQZo_BvfNMo0zRM7WPb4RXmS4Bx_rRT5utf2b6QI8o"
    
    print("🧪 Testing DIRECT FCM to known token...")
    print(f"📱 Token: {fcm_token[:30]}...")
    
    # Simulate real order data
    order_data = {
        "autoOpen": "true",
        "orderId": "888",
        "orderNumber": "REAL-ORDER-TEST",
        "amount": "999",
        "action": "autoOpenOrder",
        "forceOpen": "true"
    }
    
    print(f"📦 Data: {order_data}")
    print("🚀 Sending FCM...")
    
    success = send_data_only_message(fcm_token, order_data)
    
    if success:
        print("✅ FCM SENT! App should auto-open now!")
    else:
        print("❌ FCM FAILED!")

if __name__ == "__main__":
    test_direct_fcm()