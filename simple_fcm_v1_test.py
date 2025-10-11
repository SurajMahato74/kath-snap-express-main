#!/usr/bin/env python3
"""
Simple FCM V1 API test using service account
"""

import requests
import json
import time
from google.auth.transport.requests import Request
from google.oauth2 import service_account

# Path to your service account JSON file
SERVICE_ACCOUNT_FILE = "ezeyway-2f869-firebase-adminsdk-fbsvc-d8638b05a4.json"

# Your device FCM token
FCM_TOKEN = "c5EatI4yQPW6p7KjHDsSXu:APA916F..."

# Your Firebase project ID
PROJECT_ID = "ezeyway-2f869"

def get_access_token():
    """Get access token using service account"""
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            scopes=['https://www.googleapis.com/auth/firebase.messaging']
        )
        credentials.refresh(Request())
        return credentials.token
    except Exception as e:
        print(f"❌ Error getting access token: {e}")
        return None

def send_auto_open_fcm():
    """Send auto-open FCM message using V1 API"""
    
    access_token = get_access_token()
    if not access_token:
        return False
    
    # V1 API message format
    message = {
        "message": {
            "token": FCM_TOKEN,
            "data": {
                "autoOpen": "true",
                "orderId": "999",
                "orderNumber": "TEST-AUTO-OPEN",
                "amount": "500",
                "action": "autoOpenOrder",
                "forceOpen": "true",
                "type": "auto_open_test"
            },
            "android": {
                "priority": "high",
                "data": {
                    "autoOpen": "true",
                    "orderId": "999",
                    "orderNumber": "TEST-AUTO-OPEN",
                    "amount": "500",
                    "action": "autoOpenOrder",
                    "forceOpen": "true"
                }
            }
        }
    }
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    
    url = f'https://fcm.googleapis.com/v1/projects/{PROJECT_ID}/messages:send'
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(message))
        
        print(f"Response Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ AUTO-OPEN FCM V1 MESSAGE SENT!")
            print("📱 Close your app completely and it should auto-open in 3-5 seconds")
            return True
        else:
            print("❌ Failed to send FCM message")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 FCM V1 API Auto-Open Test")
    print("=" * 40)
    
    if FCM_TOKEN == "c5EatI4yQPW6p7KjHDsSXu:APA916F...":
        print("❌ Please update FCM_TOKEN with your actual token")
        exit(1)
    
    print("📤 Sending auto-open FCM V1 message...")
    success = send_auto_open_fcm()
    
    if success:
        print("\n✅ Test completed!")
        print("📱 Your app should auto-open now (if closed)")
    else:
        print("\n❌ Test failed!")