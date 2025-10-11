#!/usr/bin/env python3
import os
import sys
import django

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ezeyway.settings')
django.setup()

from ezeyway.accounts.firebase_init import initialize_firebase, send_fcm_message

def test_firebase():
    print("🔥 Testing Firebase with corrected file path...")
    
    # Test Firebase initialization
    if initialize_firebase():
        print("✅ Firebase initialized successfully!")
        
        # Test FCM message
        fcm_token = "c5EatI4yQPW6p7KjHDsSXu:APA91bGcxxx"  # Replace with actual token
        
        success = send_fcm_message(
            token=fcm_token,
            title="🚀 Auto-Open Test",
            body="Firebase is working! App should auto-open.",
            data={
                "action": "auto_open",
                "type": "new_order",
                "order_id": "test_123"
            }
        )
        
        if success:
            print("✅ FCM message sent successfully!")
        else:
            print("❌ Failed to send FCM message")
    else:
        print("❌ Firebase initialization failed")

if __name__ == "__main__":
    test_firebase()