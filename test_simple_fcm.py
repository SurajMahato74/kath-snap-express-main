#!/usr/bin/env python3
import os
import sys
import django

# Add the project directory to Python path
project_dir = os.path.join(os.path.dirname(__file__), 'backend', 'ezeyway')
sys.path.append(project_dir)

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ezeyway.settings')
django.setup()

from accounts.firebase_init import send_fcm_message

def test_simple_fcm():
    """Test simple FCM notification"""
    
    # Your FCM token
    fcm_token = "c5EatI4yQPW6p7KjHDsSXu:APA91bF0XRUWOs786de6AOPap9z5I5VB8k6nKOcHGzoWiGr6fzd7aQ8j3Xxxnbc7QvSY07C_Ykl6mBQZo_BvfNMo0zRM7WPb4RXmS4Bx_rRT5utf2b6QI8o"
    
    print("🚀 Testing simple FCM notification...")
    
    # Send simple notification
    data = {
        "orderId": "123",
        "orderNumber": "TEST-123",
        "customerName": "Test Customer",
        "amount": "50",
        "items": "Test items"
    }
    
    notification = {
        "title": "🔥 NEW ORDER #TEST-123",
        "body": "Test Customer • $50 • Test items"
    }
    
    try:
        success = send_fcm_message(fcm_token, data, notification)
        if success:
            print("✅ FCM notification sent successfully!")
            print("📱 Check your phone for notification")
        else:
            print("❌ FCM notification failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_simple_fcm()