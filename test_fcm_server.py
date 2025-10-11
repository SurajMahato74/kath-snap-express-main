#!/usr/bin/env python3
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/home/ezeywayc/kath-snap-express-main/backend/ezeyway')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ezeyway.settings')
django.setup()

from accounts.firebase_init import send_fcm_message

def test_fcm():
    """Test FCM notification on server"""
    
    fcm_token = "c5EatI4yQPW6p7KjHDsSXu:APA91bF0XRUWOs786de6AOPap9z5I5VB8k6nKOcHGzoWiGr6fzd7aQ8j3Xxxnbc7QvSY07C_Ykl6mBQZo_BvfNMo0zRM7WPb4RXmS4Bx_rRT5utf2b6QI8o"
    
    print("Testing FCM notification...")
    
    data = {
        "orderId": "999",
        "orderNumber": "TEST-999",
        "customerName": "Test Customer",
        "amount": "100"
    }
    
    notification = {
        "title": "🔥 NEW ORDER #TEST-999",
        "body": "Test Customer • $100"
    }
    
    try:
        success = send_fcm_message(fcm_token, data, notification)
        if success:
            print("✅ FCM sent successfully!")
        else:
            print("❌ FCM failed")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_fcm()