#!/usr/bin/env python3

import os
import sys
import django

# Add the Django project to the path
sys.path.append('c:/Users/suraj/OneDrive/Desktop/BRANDWAVE/kath-snap-express-main/backend/ezeyway')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ezeyway.settings')
django.setup()

from accounts.firebase_init import send_data_only_message

def test_aggressive_auto_open():
    """Test the new aggressive auto-open approach"""
    
    # Your FCM token
    fcm_token = "c5EatI4yQPW6p7KjHDsSXu:APA91bF0XRUWOs786de6AOPap9z5I5VB8k6nKOcHGzoWiGr6fzd7aQ8j3Xxxnbc7QvSY07C_Ykl6mBQZo_BvfNMo0zRM7WPb4RXmS4Bx_rRT5utf2b6QI8o"
    
    # Test order data
    order_data = {
        "autoOpen": "true",
        "orderId": "777",
        "orderNumber": "AGGRESSIVE-TEST",
        "amount": "2000",
        "action": "autoOpenOrder",
        "forceOpen": "true"
    }
    
    print("🚀 Testing AGGRESSIVE AUTO-OPEN...")
    print("📱 CLOSE YOUR APP COMPLETELY!")
    print("⏰ Sending in 3 seconds...")
    
    import time
    time.sleep(3)
    
    print("📡 Sending high-priority FCM...")
    
    success = send_data_only_message(fcm_token, order_data)
    
    if success:
        print("✅ AGGRESSIVE FCM SENT!")
        print("📱 App should FORCE OPEN automatically!")
        print("🔔 Check if notification appears AND app opens")
    else:
        print("❌ Failed to send FCM")

if __name__ == "__main__":
    test_aggressive_auto_open()