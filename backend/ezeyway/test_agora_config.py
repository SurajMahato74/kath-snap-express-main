#!/usr/bin/env python3
"""
Agora Token Validation Test
Run this to check if your Agora configuration is correct
"""
import sys
import os
sys.path.append('/home/ezeywayc/public_html/backend/ezeyway')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ezeyway.settings')

import django
django.setup()

from accounts.agora_service import AgoraTokenGenerator
from django.conf import settings

def test_agora_credentials():
    """Test Agora App ID and Certificate"""
    print("🔍 Testing Agora Credentials...")
    
    app_id = getattr(settings, 'AGORA_APP_ID', None)
    app_cert = getattr(settings, 'AGORA_APP_CERTIFICATE', None)
    
    print(f"📱 AGORA_APP_ID: {app_id}")
    print(f"🔐 AGORA_APP_CERTIFICATE: {'SET' if app_cert else 'NOT SET'}")
    
    # Validate App ID format
    if not app_id or len(app_id) != 32:
        print("❌ Invalid App ID format (should be 32 characters)")
        return False
        
    # Validate App Certificate format  
    if not app_cert or len(app_cert) != 32:
        print("❌ Invalid App Certificate format (should be 32 characters)")
        return False
        
    print("✅ Credentials format looks correct")
    return True

def test_token_generation():
    """Test actual token generation"""
    print("\n🔍 Testing Token Generation...")
    
    try:
        generator = AgoraTokenGenerator()
        
        # Test with same parameters as your app
        channel = "test_channel_123"
        uid = 0
        
        print(f"📋 Test Parameters:")
        print(f"  - Channel: {channel}")
        print(f"  - UID: {uid}")
        
        # Generate token
        token = generator.generate_channel_token(channel, uid)
        
        if not token:
            print("❌ Token generation returned None")
            return False
            
        print(f"\n✅ Token Generated:")
        print(f"  - Length: {len(token)} characters")
        print(f"  - Starts with 006/007: {token.startswith(('006', '007'))}")
        print(f"  - Full token: {token}")
        
        # Validate token format
        if len(token) < 100:
            print("❌ Token too short - likely invalid")
            return False
            
        if not token.startswith(('006', '007')):
            print("❌ Token doesn't start with version prefix")
            return False
            
        print("✅ Token format appears valid")
        return True
        
    except Exception as e:
        print(f"❌ Token generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multiple_tokens():
    """Test generating multiple tokens for same channel"""
    print("\n🔍 Testing Multiple Token Generation...")
    
    try:
        generator = AgoraTokenGenerator()
        channel = "call_test_123"
        
        # Generate tokens for different UIDs
        token1 = generator.generate_channel_token(channel, 0)
        token2 = generator.generate_channel_token(channel, 0)  # Same UID
        token3 = generator.generate_channel_token(channel, 1)  # Different UID
        
        print(f"Token 1 (UID=0): {token1[:50]}...")
        print(f"Token 2 (UID=0): {token2[:50]}...")
        print(f"Token 3 (UID=1): {token3[:50]}...")
        
        # Check if same UID generates same token
        if token1 == token2:
            print("✅ Same UID generates identical tokens")
        else:
            print("⚠️  Same UID generates different tokens (timestamp difference)")
            
        return True
        
    except Exception as e:
        print(f"❌ Multiple token test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Agora Configuration Test")
    print("=" * 50)
    
    # Test credentials
    creds_ok = test_agora_credentials()
    
    # Test token generation
    token_ok = test_token_generation()
    
    # Test multiple tokens
    multi_ok = test_multiple_tokens()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"  - Credentials: {'✅ PASS' if creds_ok else '❌ FAIL'}")
    print(f"  - Token Generation: {'✅ PASS' if token_ok else '❌ FAIL'}")
    print(f"  - Multiple Tokens: {'✅ PASS' if multi_ok else '❌ FAIL'}")
    
    if all([creds_ok, token_ok, multi_ok]):
        print("\n🎉 ALL TESTS PASSED!")
        print("Your Agora configuration is correct.")
        print("The issue might be in frontend token usage.")
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("Fix your Agora App ID/Certificate in Django settings.")
        
    return all([creds_ok, token_ok, multi_ok])

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)