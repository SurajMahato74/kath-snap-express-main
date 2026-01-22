#!/usr/bin/env python3
"""
Test script to debug call accept API issues
Run this to identify why the accept endpoint returns 500 error
"""

import requests
import json
import sys

# Configuration
BASE_URL = "https://ezeyway.com"
# Replace with actual tokens from your app
CALLER_TOKEN = "ad97826b63211238fa0d6f4c3f9521e071d17bea"  # User 79 token
RECEIVER_TOKEN = "145e8af3804176faf14e17200bb13cb6028ad032"  # User 2 token

def test_call_flow():
    """Test the complete call flow to identify issues"""
    
    print("🔍 Testing Call Accept API Flow...")
    print("=" * 50)
    
    # Step 1: Create a call (as caller - user 79)
    print("\n1️⃣ Creating call...")
    create_response = requests.post(
        f"{BASE_URL}/api/messaging/calls/initiate/",
        headers={
            "Authorization": f"Token {CALLER_TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "recipient_id": 2,
            "call_type": "audio"
        }
    )
    
    print(f"Create call status: {create_response.status_code}")
    if create_response.status_code == 201:
        call_data = create_response.json()
        call_id = call_data["call"]["call_id"]
        print(f"✅ Call created: {call_id}")
        print(f"📄 Response: {json.dumps(call_data, indent=2)}")
    else:
        print(f"❌ Failed to create call: {create_response.text}")
        return
    
    # Step 2: Try to accept the call (as receiver - user 2)
    print(f"\n2️⃣ Accepting call: {call_id}")
    
    # Test both possible accept endpoints
    endpoints_to_test = [
        f"/api/accounts/calls/{call_id}/accept/",  # call_api_views.py
        f"/api/messaging/calls/{call_id}/accept/"  # call_actions_api.py
    ]
    
    for endpoint in endpoints_to_test:
        print(f"\n🔍 Testing endpoint: {endpoint}")
        
        accept_response = requests.post(
            f"{BASE_URL}{endpoint}",
            headers={
                "Authorization": f"Token {RECEIVER_TOKEN}",
                "Content-Type": "application/json"
            },
            json={}
        )
        
        print(f"Accept status: {accept_response.status_code}")
        print(f"Accept response: {accept_response.text}")
        
        if accept_response.status_code == 200:
            print("✅ Accept successful!")
            response_data = accept_response.json()
            
            # Check if Agora token is included
            if "agora_token" in response_data:
                print(f"✅ Agora token included: {response_data['agora_token'][:30]}...")
            else:
                print("❌ No Agora token in response!")
                
            print(f"📄 Full response: {json.dumps(response_data, indent=2)}")
            break
        else:
            print(f"❌ Accept failed: {accept_response.text}")
    
    # Step 3: Check call status
    print(f"\n3️⃣ Checking call status...")
    status_response = requests.get(
        f"{BASE_URL}/api/messaging/calls/{call_id}/status/",
        headers={"Authorization": f"Token {RECEIVER_TOKEN}"}
    )
    
    print(f"Status check: {status_response.status_code}")
    if status_response.status_code == 200:
        print(f"📄 Call status: {status_response.json()}")
    else:
        print(f"❌ Status check failed: {status_response.text}")

def test_agora_token_generation():
    """Test Agora token generation directly"""
    
    print("\n🔍 Testing Agora Token Generation...")
    print("=" * 50)
    
    test_response = requests.post(
        f"{BASE_URL}/api/accounts/agora-token/",
        headers={
            "Authorization": f"Token {RECEIVER_TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "call_id": "test_call_123",
            "channel_name": "test_call_123",
            "uid": 0
        }
    )
    
    print(f"Token generation status: {test_response.status_code}")
    print(f"Token response: {test_response.text}")
    
    if test_response.status_code == 200:
        token_data = test_response.json()
        print(f"✅ Token generated: {token_data.get('token', 'N/A')[:30]}...")
    else:
        print(f"❌ Token generation failed")

def main():
    """Run all tests"""
    try:
        test_call_flow()
        test_agora_token_generation()
        
        print("\n" + "=" * 50)
        print("🔍 DEBUGGING TIPS:")
        print("1. Check server logs for detailed error messages")
        print("2. Verify AGORA_APP_CERTIFICATE is correct in settings")
        print("3. Ensure call_actions_api.py has Agora token generation")
        print("4. Check if the correct accept endpoint is being called")
        
    except Exception as e:
        print(f"❌ Test script error: {e}")

if __name__ == "__main__":
    main()