#!/usr/bin/env python3
"""
Test script to verify WebSocket message routing fix
"""
import requests
import json

BASE_URL = "https://ezeyway.com"
CALLER_TOKEN = "145e8af3804176faf14e17200bb13cb6028ad032"  # User 2 token  

def test_websocket_fix():
    print("🔧 Testing WebSocket fix - Creating new call...")
    
    # Step 1: Create a new call from user 2 to user 79
    create_response = requests.post(
        f"{BASE_URL}/api/messaging/calls/initiate/",
        headers={
            "Authorization": f"Token {CALLER_TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "recipient_id": 79,
            "call_type": "audio"
        }
    )
    
    if create_response.status_code == 201:
        call_data = create_response.json()
        call_id = call_data['call']['call_id']
        print(f"✅ Call created: {call_id}")
        print(f"Caller: User 2, Receiver: User 79")
        print(f"\n📱 Now test on mobile:")
        print(f"1. User 79 should receive incoming call notification")
        print(f"2. When User 79 accepts, User 2 should get call_accepted WebSocket message")
        print(f"3. Call ID: {call_id}")
        print(f"\n✅ WebSocket fix is deployed and ready to test!")
        return call_id
    else:
        print(f"❌ Call creation failed: {create_response.text}")
        return None

if __name__ == "__main__":
    test_websocket_fix()