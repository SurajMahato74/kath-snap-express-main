#!/usr/bin/env python3
"""
WebSocket server startup script for Django Channels
This ensures proper ASGI configuration for WebSocket support
"""

import os
import sys
import subprocess
import time

def main():
    """Start the Django server with WebSocket support"""
    
    # Add the project directory to Python path
    project_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(project_dir, 'backend', 'ezeyway')
    
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)
    
    print("🚀 Starting Django server with WebSocket support...")
    print(f"📁 Backend directory: {backend_dir}")
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ezeyway.settings')
    
    # Change to backend directory
    os.chdir(backend_dir)
    
    try:
        # Test Django setup
        print("🔍 Testing Django configuration...")
        import django
        django.setup()
        
        # Test Channels configuration
        from django.conf import settings
        if hasattr(settings, 'CHANNEL_LAYERS'):
            print("✅ Django Channels is configured")
            print(f"📡 Channel layer: {settings.CHANNEL_LAYERS}")
        else:
            print("❌ Django Channels not properly configured")
            return
        
        # Check if ASGI application exists
        try:
            from ezeyway.asgi import application
            print("✅ ASGI application loaded successfully")
        except ImportError as e:
            print(f"❌ ASGI application import failed: {e}")
            return
        
        print("🌐 Starting server with daphne (ASGI server for Channels)...")
        print("🔗 WebSocket endpoint: ws://localhost:8000/ws/notifications/")
        print("Press Ctrl+C to stop the server")
        
        # Start server with daphne (recommended for Channels)
        subprocess.run([
            sys.executable, '-m', 'daphne', 
            '-b', '0.0.0.0', 
            '-p', '8000', 
            'ezeyway.asgi:application'
        ])
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"💥 Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()