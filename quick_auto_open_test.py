#!/usr/bin/env python3
"""
Quick auto-open test using direct HTTP request to your Django backend
"""

import requests
import json

# Your Django backend URL
BACKEND_URL = "https://ezeyway.com"  # or your ngrok URL

# Your vendor login credentials
VENDOR_EMAIL = "your_vendor_email@example.com"
VENDOR_PASSWORD = "your_password"

def login_and_test():
    """Login as vendor and trigger auto-open test"""
    
    # Step 1: Login
    login_url = f"{BACKEND_URL}/api/accounts/vendor/login/"
    login_data = {
        "email": VENDOR_EMAIL,
        "password": VENDOR_PASSWORD
    }
    
    try:
        print("🔐 Logging in...")
        response = requests.post(login_url, json=login_data)
        
        if response.status_code != 200:
            print(f"❌ Login failed: {response.status_code}")
            print(response.text)
            return False
            
        data = response.json()
        token = data.get('token')
        
        if not token:
            print("❌ No token received")
            return False
            
        print(f"✅ Login successful! Token: {token[:20]}...")
        
        # Step 2: Send auto-open test
        test_url = f"{BACKEND_URL}/api/test-fcm-notification/"
        headers = {
            "Authorization": f"Token {token}",
            "Content-Type": "application/json"
        }
        
        test_data = {
            "title": "🚀 AUTO-OPEN TEST",
            "message": "Testing auto-open functionality!",
            "orderId": 999,
            "orderNumber": "TEST-AUTO-OPEN",
            "amount": "500"
        }
        
        print("📤 Sending auto-open test...")
        response = requests.post(test_url, headers=headers, json=test_data)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("\n✅ AUTO-OPEN TEST SENT!")
            print("📱 CLOSE YOUR APP COMPLETELY NOW!")
            print("⏰ App should auto-open in 3-5 seconds")
            return True
        else:
            print("❌ Test failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Quick Auto-Open Test")
    print("=" * 40)
    
    if VENDOR_EMAIL == "your_vendor_email@example.com":
        print("❌ Please update VENDOR_EMAIL and VENDOR_PASSWORD")
        exit(1)
    
    success = login_and_test()
    
    if success:
        print("\n🎉 Test completed!")
        print("📱 Check your mobile device")
    else:
        print("\n❌ Test failed!")