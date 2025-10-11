#!/usr/bin/env python3
"""
Fix Firebase initialization
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/home/ezeywayc/kath-snap-express-main/backend/ezeyway')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ezeyway.settings')
django.setup()

import firebase_admin
from firebase_admin import credentials, messaging

def fix_firebase():
    """Fix Firebase initialization"""
    try:
        # Clear any existing apps
        if firebase_admin._apps:
            print("🔄 Clearing existing Firebase apps...")
            for app in firebase_admin._apps.values():
                firebase_admin.delete_app(app)
        
        # Initialize with correct path
        service_account_path = '/home/ezeywayc/kath-snap-express-main/ezeyway-2f869-firebase-adminsdk-fbsvc-d8638b05a4.json'
        
        print(f"📁 Checking file: {service_account_path}")
        if not os.path.exists(service_account_path):
            print("❌ Service account file not found!")
            return False
        
        print("🔥 Initializing Firebase...")
        cred = credentials.Certificate(service_account_path)
        app = firebase_admin.initialize_app(cred)
        
        print(f"✅ Firebase initialized successfully: {app.name}")
        
        # Test sending a message
        test_token = "c5EatI4yQPW6p7KjHDsSXu:APA91bF0XRUWOs786de6AOPap9z5I5VB8k6nKOcHGzoWiGr6fzd7aQ8j3Xxxnbc7QvSY07C_Ykl6mBQZo_BvfNMo0zRM7WPb4RXmS4Bx_rRT5utf2b6QI8o"  # Your actual FCM token
        
        message = messaging.Message(
            data={
                "autoOpen": "true",
                "orderId": "999",
                "orderNumber": "TEST-AUTO-OPEN",
                "amount": "500",
                "action": "autoOpenOrder",
                "forceOpen": "true"
            },
            token=test_token,
            android=messaging.AndroidConfig(
                priority='high'
            )
        )
        
        print("📤 Sending test message...")
        response = messaging.send(message)
        print(f"✅ Message sent successfully: {response}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Firebase Fix Script")
    print("=" * 30)
    fix_firebase()