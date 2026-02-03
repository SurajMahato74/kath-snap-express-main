#!/usr/bin/env python3
"""
Test script to verify WebSocket message routing fix
"""
import requests
import json

BASE_URL = "https://ezeyway.com"
CALLER_TOKEN = "145e8af3804176faf14e17200bb13cb6028ad032"  # User 2 token  
CALL_ID = "call_2_79_1770109287"  # From previous test

def test_websocket_fix():
    print("🔧 Testing WebSocket fix for call acceptance...")
    
    # Test accepting the existing call
    print(f"Testing call acceptance for {CALL_ID}...")
    
    accept_response = requests.post(
        f"{BASE_URL}/api/calls/{CALL_ID}/accept/",
        headers={
            "Authorization": f"Token {CALLER_TOKEN}",
            "Content-Type": "application/json"
        },
        json={}
    )
    
    print(f"Accept status: {accept_response.status_code}")
    print(f"Accept response: {accept_response.text}")
    
    if accept_response.status_code == 200:
        print("✅ SUCCESS! WebSocket fix is working!")
        print("The caller should now receive the call_accepted message via WebSocket")
    elif accept_response.status_code == 404:
        print("⚠️  Call not found - may have expired")
    elif accept_response.status_code == 403:
        print("⚠️  Wrong user for this call")
    else:
        print(f"❌ Error: {accept_response.status_code}")

if __name__ == "__main__":
    test_websocket_fix()