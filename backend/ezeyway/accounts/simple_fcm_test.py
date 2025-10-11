#!/usr/bin/env python3
"""
Simple FCM test without Firebase Admin SDK
"""

import requests
import json

def send_simple_fcm_test(fcm_token):
    """Send FCM using legacy API (works without service account)"""
    
    # Use legacy FCM API (still works for testing)
    url = "https://fcm.googleapis.com/fcm/send"
    
    # Temporary server key for testing (replace with yours)
    server_key = "AAAAyOu_Your_Server_Key_Here"
    
    headers = {
        'Authorization': f'key {server_key}',
        'Content-Type': 'application/json',
    }
    
    # Auto-open message
    message = {
        "to": fcm_token,
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
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(message))
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ FCM sent successfully!")
            return True
        else:
            print("❌ FCM failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

# Test with your token
if __name__ == "__main__":
    token = "c5EatI4yQPW6p7KjHDsSXu:APA916F..."  # Your actual token
    send_simple_fcm_test(token)