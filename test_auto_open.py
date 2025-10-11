#!/usr/bin/env python3
"""
Test script to trigger auto-open FCM messages
"""

import requests
import json
import time

# Configuration
API_BASE = "https://ezeyway.com"
# Replace with your vendor login credentials
VENDOR_EMAIL = "vendor@example.com"
VENDOR_PASSWORD = "password123"

def login_vendor():
    """Login as vendor and get auth token"""
    login_url = f"{API_BASE}/api/accounts/vendor/login/"
    
    login_data = {
        "email": VENDOR_EMAIL,
        "password": VENDOR_PASSWORD
    }
    
    try:
        response = requests.post(login_url, json=login_data)
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token') or data.get('token')
            print(f"✅ Vendor login successful! Token: {token[:20]}...")
            return token
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def send_auto_open_test(token):
    """Send auto-open test notification"""
    test_url = f"{API_BASE}/api/notifications/test-auto-open/"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(test_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"🚀 AUTO-OPEN TEST SENT!")
            print(f"Response: {json.dumps(data, indent=2)}")
            print(f"\n⚠️ CLOSE THE APP COMPLETELY NOW!")
            print(f"The app should auto-open in 3-5 seconds without tapping anything.")
            return True
        else:
            print(f"❌ Test failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

def main():
    print("🧪 Auto-Open Test Script")
    print("=" * 40)
    
    # Login
    print("1. Logging in as vendor...")
    token = login_vendor()
    if not token:
        return
    
    # Wait a moment
    time.sleep(1)
    
    # Send test
    print("\n2. Sending auto-open test...")
    success = send_auto_open_test(token)
    
    if success:
        print("\n✅ Test completed successfully!")
        print("📱 Check your mobile device - the app should auto-open")
    else:
        print("\n❌ Test failed!")

if __name__ == "__main__":
    main()