#!/usr/bin/env python
"""
Start Django server with WebSocket support using Daphne
"""
import os
import sys
import subprocess

def main():
    # Set Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ezeyway.settings')
    
    # Change to the Django project directory
    project_dir = os.path.join(os.path.dirname(__file__), 'ezeyway')
    os.chdir(project_dir)
    
    print("Starting Django server with WebSocket support...")
    print("Server will be available at: http://localhost:8000")
    print("WebSocket endpoint: ws://localhost:8000/ws/notifications/")
    print("Press Ctrl+C to stop the server")
    print("-" * 50)
    
    try:
        # Try to start with daphne (ASGI server for WebSocket support)
        subprocess.run([
            sys.executable, 'manage.py', 'runserver', '0.0.0.0:8000'
        ], check=True)
    except subprocess.CalledProcessError:
        print("Error: Failed to start server")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        sys.exit(0)

if __name__ == '__main__':
    main()