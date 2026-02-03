#!/usr/bin/env python3
"""
Test script to verify WebSocket message routing fix
"""
import requests
import json

BASE_URL = "https://ezeyway.com"
CALLER_TOKEN = "145e8af3804176faf14e17200bb13cb6028ad032"  # User 2 token  
RECEIVER_TOKEN = "another_token_here"  # User 79 token

def test_call_flow():
    print("🧪 Testing complete call flow with WebSocket fix...")
    
    # Step 1: Create call
    print("\n1️⃣ Creating call...")
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
        
        # Step 2: Accept call (this should now send WebSocket to caller)
        print(f"\n2️⃣ Accepting call {call_id}...")
        accept_response = requests.post(
            f"{BASE_URL}/api/calls/{call_id}/accept/",
            headers={
                "Authorization": f"Token {RECEIVER_TOKEN}",
                "Content-Type": "application/json"
            },
            json={}
        )
        
        print(f"Accept status: {accept_response.status_code}")
        print(f"Accept response: {accept_response.text}")
        
        if accept_response.status_code == 200:
            print("✅ Call accepted - WebSocket should be sent to caller now!")
            return call_id
        else:
            print("❌ Call accept failed")
            return None
    else:
        print(f"❌ Call creation failed: {create_response.text}")
        return None

if __name__ == "__main__":
    test_call_flow()