#!/usr/bin/env python3
"""
Test Agora Token Generation
Run this to verify Agora settings and token generation
"""

import os
import sys
import django

# Add the project path
sys.path.append('/opt/ezeyway/kath-snap-express-main/backend/ezeyway')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ezeyway.settings')
django.setup()

from accounts.agora_service import AgoraTokenGenerator
from django.conf import settings

def test_agora_config():
    print("🔧 Testing Agora Configuration...")
    
    # Check settings
    app_id = getattr(settings, 'AGORA_APP_ID', None)
    app_cert = getattr(settings, 'AGORA_APP_CERTIFICATE', None)
    
    print(f"📱 AGORA_APP_ID: {app_id}")
    print(f"🔐 AGORA_APP_CERTIFICATE: {'SET' if app_cert else 'NOT SET'}")
    
    if not app_id or not app_cert:
        print("❌ Agora credentials not properly configured!")
        return False
    
    # Test token generation
    try:
        generator = AgoraTokenGenerator()
        token = generator.generate_channel_token("test_channel", 123)
        print(f"✅ Token generated successfully: {token[:20]}...")
        return True
    except Exception as e:
        print(f"❌ Token generation failed: {e}")
        return False

if __name__ == "__main__":
    test_agora_config()