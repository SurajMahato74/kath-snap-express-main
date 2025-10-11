#!/usr/bin/env python3
"""
Simple FCM test using HTTP requests (no Firebase Admin SDK needed)
"""

import requests
import json

# Your FCM Server Key from Firebase Console > Project Settings > Cloud Messaging
FCM_SERVER_KEY = "AAAAyOu_Your_FCM_Server_Key_Here"

# Your device FCM token (from the app debug info)
FCM_TOKEN = "c5EatI4yQPW6p7KjHDsSXu:APA916F..."

def send_auto_open_fcm():
    """Send auto-open FCM message directly"""
    
    # Data-only message for auto-opening
    message = {
        "to": FCM_TOKEN,
        "priority": "high",
        "data": {
            "autoOpen": "true",
            "orderId": "999",
            "orderNumber": "TEST-AUTO-OPEN",
            "amount": "500",
            "action": "autoOpenOrder",
            "forceOpen": "true",
            "type": "auto_open_test"
        }
    }
    
    headers = {
        'Authorization': f'key {FCM_SERVER_KEY}',
        'Content-Type': 'application/json',
    }
    
    try:
        response = requests.post(
            'https://fcm.googleapis.com/fcm/send',
            headers=headers,
            data=json.dumps(message)
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ AUTO-OPEN FCM MESSAGE SENT!")
            print("📱 Close your app completely and it should auto-open in 3-5 seconds")
            return True
        else:
            print("❌ Failed to send FCM message")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Simple FCM Auto-Open Test")
    print("=" * 40)
    
    if FCM_SERVER_KEY == "AAAAyOu_Your_FCM_Server_Key_Here":
        print("❌ Please update FCM_SERVER_KEY with your actual key")
        exit(1)
    
    if FCM_TOKEN == "c5EatI4yQPW6p7KjHDsSXu:APA916F...":
        print("❌ Please update FCM_TOKEN with your actual token")
        exit(1)
    
    print("📤 Sending auto-open FCM message...")
    success = send_auto_open_fcm()
    
    if success:
        print("\n✅ Test completed!")
        print("📱 Your app should auto-open now (if closed)")
    else:
        print("\n❌ Test failed!")
