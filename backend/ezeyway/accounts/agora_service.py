"""
Agora Token Generation Service
Production-ready token generation using official SDK
"""

import time
import json
from django.conf import settings
from django.http import JsonResponse
from agora_token_builder import RtcTokenBuilder

class AgoraTokenGenerator:
    def __init__(self):
        self.app_id = settings.AGORA_APP_ID
        self.app_certificate = settings.AGORA_APP_CERTIFICATE
        
        if not self.app_id or not self.app_certificate:
            raise ValueError("AGORA_APP_ID and AGORA_APP_CERTIFICATE must be set in Django settings")
    
    def generate_channel_token(self, channel_name, uid, role=1, expire_sec=7200):
        """Generate production-ready Agora token"""
        current_time = int(time.time())
        privilege_expire_ts = current_time + expire_sec
        
        # Use role constants from RtcTokenBuilder
        agora_role = RtcTokenBuilder.RolePublisher if role == 1 else RtcTokenBuilder.RoleSubscriber
        
        token = RtcTokenBuilder.build_token_with_uid(
            app_id=self.app_id,
            app_certificate=self.app_certificate,
            channel_name=str(channel_name),
            uid=int(uid),
            role=agora_role,
            privilege_expire_ts=privilege_expire_ts
        )
        return token
    
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