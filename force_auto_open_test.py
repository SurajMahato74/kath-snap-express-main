#!/usr/bin/env python3
import os
import sys
import django

# Add the Django project to Python path
sys.path.append('/home/ezeywayc/kath-snap-express-main/backend/ezeyway')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ezeyway.settings')
django.setup()

from accounts.firebase_init import send_fcm_message

def send_force_auto_open():
    """Send FCM with maximum priority and full-screen intent"""
    
    print("🚀 Sending Force Auto-Open FCM")
    print("=" * 35)
    
    fcm_token = "c5EatI4yQPW6p7KjHDsSXu:APA91bF0XRUWOs786de6AOPap9z5I5VB8k6nKOcHGzoWiGr6fzd7aQ8j3Xxxnbc7QvSY07C_Ykl6mBQZo_BvfNMo0zRM7WPb4RXmS4Bx_rRT5utf2b6QI8o"
    
    # Maximum priority data for auto-open
    data = {
        'auto_open': 'true',
        'force_launch': 'true',
        'priority': 'high',
        'order_id': 'URGENT_ORDER_123',
        'action': 'force_open'
    }
    
    # High priority notification
    notification = {
        'title': '🔥 URGENT ORDER - AUTO OPEN',
        'body': 'New order requires immediate attention!'
    }
    
    print(f"📱 Sending to: {fcm_token[:20]}...")
    print(f"📤 Data: {data}")
    
    try:
        response = send_fcm_message(
            token=fcm_token,
            title=notification['title'],
            body=notification['body'],
            data=data
        )
        
        if response:
            print(f"✅ Force auto-open FCM sent!")
            print(f"   Response: {response}")
            print("\n🎯 Expected behavior:")
            print("   - High priority notification")
            print("   - App should force open")
            print("   - Full screen alert")
        else:
            print("❌ Failed to send FCM")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    send_force_auto_open()