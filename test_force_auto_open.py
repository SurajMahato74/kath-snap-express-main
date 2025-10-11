#!/usr/bin/env python3

import os
import sys
import django

# Add the Django project to the path
sys.path.append('c:/Users/suraj/OneDrive/Desktop/BRANDWAVE/kath-snap-express-main/backend/ezeyway')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ezeyway.settings')
django.setup()

from accounts.firebase_init import send_data_only_message

def test_force_auto_open():
    """Test aggressive auto-open that doesn't require user tap"""
    
    # Your FCM token
    fcm_token = "c5EatI4yQPW6p7KjHDsSXu:APA91bF0XRUWOs786de6AOPap9z5I5VB8k6nKOcHGzoWiGr6fzd7aQ8j3Xxxnbc7QvSY07C_Ykl6mBQZo_BvfNMo0zRM7WPb4RXmS4Bx_rRT5utf2b6QI8o"
    
    # Test order data
    order_data = {
        "autoOpen": "true",
        "autoLaunch": "true", 
        "orderId": "999",
        "orderNumber": "FORCE-AUTO-OPEN",
        "amount": "1500",
        "action": "autoOpenOrder",
        "forceOpen": "true"
    }
    
    print("🚀 Testing FORCE AUTO-OPEN (no user tap needed)...")
    print("📱 CLOSE YOUR APP COMPLETELY NOW!")
    print("⏰ Sending in 5 seconds...")
    
    import time
    time.sleep(5)
    
    print(f"📦 Sending: {order_data}")
    
    # Send the aggressive auto-open message
    success = send_data_only_message(fcm_token, order_data)
    
    if success:
        print("✅ FORCE AUTO-OPEN SENT!")
        print("📱 App should open automatically WITHOUT tapping notification!")
        print("🔔 You'll see notification + app opens by itself")
    else:
        print("❌ Failed to send")

if __name__ == "__main__":
    test_force_auto_open()