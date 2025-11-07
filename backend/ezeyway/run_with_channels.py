#!/usr/bin/env python
import os
import sys
import django
import subprocess
from django.core.management import execute_from_command_line

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ezeyway.settings')
    
    # For WebSocket support, use daphne instead of runserver
    if len(sys.argv) > 1 and sys.argv[1] == 'runserver':
        print("🚀 Starting server with Daphne for WebSocket support...")
        print("📡 WebSocket endpoint: ws://localhost:8000/ws/notifications/")
        
        try:
            # Use daphne which supports both HTTP and WebSocket
            subprocess.run([
                sys.executable, '-m', 'daphne',
                '-b', '0.0.0.0',
                '-p', '8000',
                'ezeyway.asgi:application'
            ])
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")
        except Exception as e:
            print(f"💥 Error with daphne, falling back to runserver: {e}")
            execute_from_command_line(['manage.py', 'runserver', '--noreload'])
    else:
        execute_from_command_line(sys.argv)