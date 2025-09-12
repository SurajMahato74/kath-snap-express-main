#!/usr/bin/env python3
"""
Test script to verify image upload functionality
Run this from the backend directory: python test_image_upload.py
"""

import requests
import os

# Configuration
API_BASE_URL = 'http://localhost:8000'
TOKEN = 'your_auth_token_here'  # Replace with actual token

def test_image_upload():
    """Test image upload with a real file"""
    
    # Create a test image file if it doesn't exist
    test_image_path = 'test_image.png'
    if not os.path.exists(test_image_path):
        # Create a simple 1x1 pixel PNG
        import base64
        png_data = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU77yQAAAABJRU5ErkJggg==')
        with open(test_image_path, 'wb') as f:
            f.write(png_data)
    
    # Test product creation with image
    headers = {
        'Authorization': f'Token {TOKEN}',
    }
    
    data = {
        'name': 'Test Product with Image',
        'category': 'test',
        'price': '10.00',
        'quantity': '5',
        'description': 'Test product for image upload',
        'status': 'active',
        'featured': 'false',
        'dynamic_fields': '{}',
        'tags': '[]'
    }
    
    files = {
        'image_files': open(test_image_path, 'rb')
    }
    
    try:
        response = requests.post(f'{API_BASE_URL}/products/', headers=headers, data=data, files=files)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 201:
            print("✅ Image upload successful!")
            product_data = response.json()
            if 'images' in product_data and len(product_data['images']) > 0:
                image_url = product_data['images'][0]['image_url']
                print(f"Image URL: {image_url}")
                if 'blob:' in image_url:
                    print("❌ Still getting blob URLs - check backend configuration")
                else:
                    print("✅ Proper image URL generated")
        else:
            print("❌ Upload failed")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        files['image_files'].close()
        # Clean up test file
        if os.path.exists(test_image_path):
            os.remove(test_image_path)

if __name__ == '__main__':
    print("Testing image upload functionality...")
    print("Make sure to:")
    print("1. Update TOKEN variable with your actual auth token")
    print("2. Ensure Django server is running on localhost:8000")
    print("3. Run from the backend directory")
    print()
    test_image_upload()