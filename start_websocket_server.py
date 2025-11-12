#!/usr/bin/env python
"""
Start Django server with proper WebSocket support using Daphne
"""
import os
import sys
import subprocess
import importlib.util

def check_daphne():
    """Check if Daphne is installed"""
    try:
        import daphne
        return True
    except ImportError:
        return False

def install_daphne():
    """Install Daphne if not available"""
    print("Daphne not found. Installing...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "daphne"])
        print("✅ Daphne installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install Daphne")
        return False

def main():
    # Set Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ezeyway.settings')
    
    # Change to the Django project directory
    project_dir = os.path.join(os.path.dirname(__file__), 'backend', 'ezeyway')
    os.chdir(project_dir)
    
    print("🚀 Starting Django server with WebSocket support...")
    print("=" * 60)
    print("📡 Server: http://localhost:8000")
    print("🔌 WebSocket: ws://localhost:8000/ws/notifications/")
    print("💬 Messages: ws://localhost:8000/ws/messages/")
    print("📞 Calls: ws://localhost:8000/ws/calls/")
    print("=" * 60)
    
    # Check if Daphne is available
    if not check_daphne():
        print("⚠️ Daphne not found. Installing...")
        if not install_daphne():
            print("❌ Could not install Daphne. Please install manually:")
            print("   pip install daphne")
            return False
    
    try:
        # Use Daphne (ASGI server) for WebSocket support
        print("🔥 Starting Daphne ASGI server...")
        # Set up environment and path before starting
        env = os.environ.copy()
        env['DJANGO_SETTINGS_MODULE'] = 'ezeyway.settings'
        env['PYTHONPATH'] = project_dir
        
        subprocess.run([
            sys.executable, '-m', 'daphne',
            '-b', '0.0.0.0',
            '-p', '8000',
            'ezeyway.asgi:application'
        ], check=True, env=env, cwd=project_dir)
        
    except subprocess.CalledProcessError:
        print("❌ Error: Failed to start server")
        return False
    except KeyboardInterrupt:
        print("\n✅ Server stopped by user")
        return True
    
    return False

if __name__ == '__main__':
    main()