"""
Agora Token Generation Service
Compatible with different agora-token-builder versions
"""

import time
import json
import hmac
import hashlib
import struct
import base64
from django.conf import settings
from django.http import JsonResponse

try:
    from agora_token_builder import RtcTokenBuilder
    AGORA_SDK_AVAILABLE = True
except ImportError:
    AGORA_SDK_AVAILABLE = False

class AgoraTokenGenerator:
    def __init__(self):
        self.app_id = settings.AGORA_APP_ID
        self.app_certificate = settings.AGORA_APP_CERTIFICATE
        
        if not self.app_id or not self.app_certificate:
            raise ValueError("AGORA_APP_ID and AGORA_APP_CERTIFICATE must be set in Django settings")
    
    def generate_channel_token(self, channel_name, uid, role=1, expire_sec=7200):
        """Generate Agora token with fallback methods"""
        if AGORA_SDK_AVAILABLE:
            return self._generate_with_sdk(channel_name, uid, role, expire_sec)
        else:
            return self._generate_fallback(channel_name, uid, expire_sec)
    
    def _generate_with_sdk(self, channel_name, uid, role, expire_sec):
        """Generate token using official Agora SDK"""
        current_time = int(time.time())
        privilege_expire_ts = current_time + expire_sec
        
        # Debug logging
        print(f"🔍 Generating Agora token:")
        print(f"  - App ID: {self.app_id}")
        print(f"  - App Certificate: {self.app_certificate[:8]}...{self.app_certificate[-4:]}")
        print(f"  - Channel: {channel_name}")
        print(f"  - UID: {uid}")
        print(f"  - Role: {role}")
        print(f"  - Expires in: {expire_sec} seconds")
        print(f"  - Expiry timestamp: {privilege_expire_ts}")
        
        try:
            # Use the correct method name for agora-token-builder
            token = RtcTokenBuilder.buildTokenWithUid(
                self.app_id,
                self.app_certificate,
                channel_name,
                uid,
                role,
                privilege_expire_ts
            )
            print(f"✅ Token generated successfully: {len(token)} chars")
            print(f"✅ Token preview: {token[:30]}...")
            return token
        except Exception as e:
            print(f"❌ SDK token generation failed: {e}")
            # Fall back to manual generation
            return self._generate_fallback(channel_name, uid, expire_sec)
    
    def _generate_fallback(self, channel_name, uid, expire_sec):
        """Fallback token generation using basic algorithm"""
        current_time = int(time.time())
        privilege_expire_time = current_time + expire_sec
        
        # Basic token structure
        version = '007'
        message_raw = struct.pack('<I', len(self.app_id)) + self.app_id.encode()
        message_raw += struct.pack('<I', len(channel_name)) + channel_name.encode()
        message_raw += struct.pack('<I', int(uid))
        message_raw += struct.pack('<I', privilege_expire_time)
        
        signature = hmac.new(
            self.app_certificate.encode(),
            message_raw,
            hashlib.sha256
        ).digest()
        
        token_raw = version.encode() + signature + message_raw
        return base64.b64encode(token_raw).decode()
    
    def generate_rtc_token(self, channel_name, uid=0, role=1, expire_time=7200):
        """Legacy method for backward compatibility"""
        return self.generate_channel_token(channel_name, uid, role, expire_time)

# API Views
def generate_agora_token_api(request):
    """Generate Agora token for call"""
    if request.method == 'POST':
        data = json.loads(request.body)
        channel_name = data.get('channel_name')
        uid = data.get('uid', 0)
        
        if not channel_name:
            return JsonResponse({'error': 'Channel name required'}, status=400)
        
        token_generator = AgoraTokenGenerator()
        token = token_generator.generate_rtc_token(channel_name, uid)
        
        return JsonResponse({
            'success': True,
            'token': token,
            'channel_name': channel_name,
            'uid': uid,
            'app_id': token_generator.app_id
        })
    
    return JsonResponse({'error': 'POST required'}, status=405)