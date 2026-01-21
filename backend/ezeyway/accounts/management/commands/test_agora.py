"""
Django management command to test Agora configuration
Usage: python manage.py test_agora
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from accounts.agora_service import AgoraTokenGenerator

class Command(BaseCommand):
    help = 'Test Agora token generation configuration'

    def handle(self, *args, **options):
        self.stdout.write("🔧 Testing Agora Configuration...")
        
        # Check settings
        app_id = getattr(settings, 'AGORA_APP_ID', None)
        app_cert = getattr(settings, 'AGORA_APP_CERTIFICATE', None)
        
        self.stdout.write(f"📱 AGORA_APP_ID: {app_id}")
        self.stdout.write(f"🔐 AGORA_APP_CERTIFICATE: {'SET' if app_cert else 'NOT SET'}")
        
        if not app_id or not app_cert:
            self.stdout.write(self.style.ERROR("❌ Agora credentials not properly configured!"))
            self.stdout.write("Add these to your settings.py:")
            self.stdout.write("AGORA_APP_ID = '51aafec601fa444581210f9fac99a73a'")
            self.stdout.write("AGORA_APP_CERTIFICATE = '0c85813471a1416cadab8a3d77d4fc7f'")
            return
        
        # Test token generation
        try:
            generator = AgoraTokenGenerator()
            token = generator.generate_channel_token("test_channel", 123)
            self.stdout.write(self.style.SUCCESS(f"✅ Token generated successfully: {token[:20]}..."))
            self.stdout.write("🎉 Agora configuration is working!")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Token generation failed: {e}"))