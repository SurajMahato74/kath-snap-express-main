import subprocess
import time

def test_oneplus_settings():
    """Test script to help user configure OnePlus/Oppo settings for auto-open"""
    
    print("🔧 OnePlus/Oppo Auto-Open Configuration Guide")
    print("=" * 50)
    
    print("\n📱 Your device is freezing the app. Follow these steps:")
    
    print("\n1. Open Settings > Battery > Battery Optimization")
    print("   - Find 'Ezeyway' app")
    print("   - Select 'Don't optimize'")
    
    print("\n2. Open Settings > Apps > App Management")
    print("   - Find 'Ezeyway' app")
    print("   - Go to 'Permissions'")
    print("   - Enable 'Display over other apps'")
    
    print("\n3. Open Settings > Apps > Startup Manager")
    print("   - Find 'Ezeyway' app") 
    print("   - Enable 'Auto-launch'")
    
    print("\n4. Open Settings > Privacy > Special App Access")
    print("   - Find 'Device admin apps'")
    print("   - Enable for Ezeyway if available")
    
    print("\n5. Try opening the app and keeping it in recent apps")
    
    print("\n🚀 After completing these steps, test the FCM notification again")
    
    # Try to open battery settings directly
    try:
        print("\n⚡ Attempting to open battery optimization settings...")
        subprocess.run([
            "adb", "shell", "am", "start", 
            "-a", "android.settings.IGNORE_BATTERY_OPTIMIZATION_SETTINGS"
        ], check=True)
        print("✅ Battery settings opened successfully")
    except:
        print("❌ Could not open settings automatically")
        print("   Please open Settings > Battery > Battery Optimization manually")

if __name__ == "__main__":
    test_oneplus_settings()