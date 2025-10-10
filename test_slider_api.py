#!/usr/bin/env python3
"""
Test script to verify the slider API functionality
"""

import requests
import json

# API base URL - adjust if needed
BASE_URL = "http://localhost:8000/api"

def test_slider_api():
    """Test the slider API endpoints"""
    
    print("🧪 Testing Slider API...")
    print("=" * 50)
    
    # Test 1: Get sliders for customer
    print("\n1. Testing customer sliders...")
    try:
        response = requests.get(f"{BASE_URL}/sliders/?user_type=customer")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Success: {data.get('success', False)}")
            print(f"   User Type: {data.get('user_type', 'N/A')}")
            print(f"   Slider Count: {data.get('count', 0)}")
            
            sliders = data.get('sliders', [])
            if sliders:
                print("   Sliders found:")
                for slider in sliders:
                    print(f"     - {slider['title']} (visibility: {slider['visibility']})")
            else:
                print("   No sliders found for customers")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test 2: Get sliders for vendor
    print("\n2. Testing vendor sliders...")
    try:
        response = requests.get(f"{BASE_URL}/sliders/?user_type=vendor")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Success: {data.get('success', False)}")
            print(f"   User Type: {data.get('user_type', 'N/A')}")
            print(f"   Slider Count: {data.get('count', 0)}")
            
            sliders = data.get('sliders', [])
            if sliders:
                print("   Sliders found:")
                for slider in sliders:
                    print(f"     - {slider['title']} (visibility: {slider['visibility']})")
            else:
                print("   No sliders found for vendors")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Test 3: Get all sliders (default)
    print("\n3. Testing default sliders...")
    try:
        response = requests.get(f"{BASE_URL}/sliders/")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Success: {data.get('success', False)}")
            print(f"   User Type: {data.get('user_type', 'N/A')}")
            print(f"   Slider Count: {data.get('count', 0)}")
            
            sliders = data.get('sliders', [])
            if sliders:
                print("   Sliders found:")
                for slider in sliders:
                    print(f"     - {slider['title']} (visibility: {slider['visibility']})")
            else:
                print("   No sliders found")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Slider API test completed!")
    print("\nTo add test sliders, go to:")
    print("http://localhost:8000/admin/accounts/slider/")
    print("or")
    print("http://localhost:8000/manage-sliders/")

if __name__ == "__main__":
    test_slider_api()