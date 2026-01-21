#!/usr/bin/env python3
"""
Test FCM Call Notification - Will open app and show call screen
Run this on server to test if app opens with call notification
"""

import requests
import json

# Your app's FCM token from the logs
FCM_TOKEN = "fKU99FPEROWgsA1fVz2lZg:APA91bH3Mb-FvFKZLM71uCknLWkNDr3JgysZ3aR87lrGwD_rycorJ1X2J2Z4bUV8lGhA0sDijfwabL4h1aiyIX_JYNaquRAn6hjNj75PxacdbyRl7HQq-V0"

# User ID from logs (user 79)
USER_ID = 79

# Auth token for user 79
AUTH_TOKEN = "a98e70b1f6beb3b3dcdfdaa29e261a8080a8b494"

def test_fcm_call_notification():
    """Send FCM call notification to mobile app"""
    
    print("🚀 Testing FCM Call Notification")
    print("📱 This should open your app and show call screen!")
    print("-" * 50)
    
    url = "https://ezeyway.com/api/messaging/test-fcm-call/"
    
    headers = {
        'Authorization': f'Token {AUTH_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'fcm_token': FCM_TOKEN,
        'caller_name': 'Test Server Call'
    }
    
    try:
        print(f"📤 Sending FCM notification to token: {FCM_TOKEN[:30]}...")
        
        response = requests.post(url, headers=headers, json=data)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📋 Response: {response.text}")
        
        if response.status_code == 200:
            print("\n✅ SUCCESS!")
            print("📱 CHECK YOUR PHONE NOW!")
            print("🔔 App should open with incoming call screen")
            print("📞 Caller: 'Test Server Call'")
        else:
            print(f"\n❌ FAILED: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_create_real_call():
    """Create a real call (will also trigger FCM)"""
    
    print("\n🚀 Testing Real Call Creation")
    print("📱 This will create actual call + FCM notification!")
    print("-" * 50)
    
    url = "https://ezeyway.com/api/messaging/create-call/"
    
    headers = {
        'Authorization': f'Token {AUTH_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    # Call user 2 (from the logs)
    data = {
        'recipient_id': 2,
        'call_type': 'audio'
    }
    
    try:
        print(f"📤 Creating call from user {USER_ID} to user 2...")
        
        response = requests.post(url, headers=headers, json=data)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📋 Response: {response.text}")
        
        if response.status_code == 201:
            print("\n✅ CALL CREATED!")
            print("📱 CHECK YOUR PHONE NOW!")
            print("🔔 App should open with incoming call screen")
            print("📞 Real call initiated!")
        else:
            print(f"\n❌ FAILED: {response.status_code}")
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🎯 FCM Call Notification Test")
    print("=" * 60)
    print(f"📱 Target FCM Token: {FCM_TOKEN[:30]}...")
    print(f"👤 User ID: {USER_ID}")
    print("=" * 60)
    
    # Test 1: Direct FCM notification
    test_fcm_call_notification()
    
    # Wait for user input before real call test
    input("\n⏸️  Press Enter to test REAL call creation...")
    
    # Test 2: Real call creation
    test_create_real_call()
    
    print("\n🎉 Test completed!")
    print("📱 Check your phone for notifications!")