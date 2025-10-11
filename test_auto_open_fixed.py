#!/usr/bin/env python3

import requests
import json

# Test the fixed auto-open functionality
def test_auto_open():
    base_url = "http://localhost:8000"
    
    # Test data
    test_data = {
        "title": "New Order Alert!",
        "message": "You have received a new order",
        "orderId": 123,
        "orderNumber": "ORD-123",
        "amount": "750"
    }
    
    print("🧪 Testing Auto-Open FCM Notification...")
    print(f"📡 Sending to: {base_url}/api/test-fcm-notification/")
    print(f"📦 Data: {json.dumps(test_data, indent=2)}")
    
    try:
        # You'll need to add authentication headers here
        headers = {
            'Content-Type': 'application/json',
            # 'Authorization': 'Token YOUR_VENDOR_TOKEN_HERE'
        }
        
        response = requests.post(
            f"{base_url}/api/test-fcm-notification/",
            json=test_data,
            headers=headers,
            timeout=10
        )
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📄 Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Auto-open test notification sent successfully!")
        else:
            print("❌ Failed to send notification")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_auto_open()