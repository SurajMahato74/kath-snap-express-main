from django.core.management.base import BaseCommand
from django.conf import settings
from accounts.agora_service import AgoraTokenGenerator

class Command(BaseCommand):
    help = 'Test Agora token generation'

    def handle(self, *args, **options):
        self.stdout.write("🔍 Testing Agora Configuration...")
        
        # Check settings
        app_id = getattr(settings, 'AGORA_APP_ID', None)
        app_cert = getattr(settings, 'AGORA_APP_CERTIFICATE', None)
        
        self.stdout.write(f"App ID: {app_id}")
        self.stdout.write(f"App Certificate: {'SET' if app_cert and app_cert != 'your_agora_app_certificate_here' else 'NOT SET'}")
        
        if not app_cert or app_cert == 'your_agora_app_certificate_here':
            self.stdout.write(self.style.ERROR("❌ AGORA_APP_CERTIFICATE not configured"))
            return
            
        # Test token generation
        try:
            generator = AgoraTokenGenerator()
            token = generator.generate_channel_token("test_call_123", 0, 7200)
            
            self.stdout.write(f"✅ Token generated: {len(token)} chars")
            self.stdout.write(f"✅ Token preview: {token[:30]}...")
            self.stdout.write(f"✅ Valid format: {token.startswith(('006', '007'))}")
            
            if len(token) > 100 and token.startswith(('006', '007')):
                self.stdout.write(self.style.SUCCESS("🎉 Agora configuration is working!"))
            else:
                self.stdout.write(self.style.ERROR("❌ Invalid token format"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Token generation failed: {e}"))