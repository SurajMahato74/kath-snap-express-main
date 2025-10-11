#!/usr/bin/env python3

import os
import sys
import django

# Add the Django project to the path
sys.path.append('c:/Users/suraj/OneDrive/Desktop/BRANDWAVE/kath-snap-express-main/backend/ezeyway')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ezeyway.settings')
django.setup()

from accounts.models import VendorProfile

def debug_vendor_fcm():
    """Debug vendor FCM tokens"""
    
    print("🔍 Checking all vendor FCM tokens...")
    
    vendors = VendorProfile.objects.all()
    
    for vendor in vendors:
        print(f"\n📊 Vendor: {vendor.business_name}")
        print(f"   User: {vendor.user.username}")
        print(f"   Approved: {vendor.is_approved}")
        print(f"   Active: {vendor.is_active}")
        print(f"   FCM Token: {vendor.fcm_token[:30] + '...' if vendor.fcm_token else 'NONE'}")
        print(f"   FCM Updated: {vendor.fcm_updated_at}")
    
    # Check if there are any vendors with FCM tokens
    vendors_with_fcm = VendorProfile.objects.exclude(fcm_token__isnull=True).exclude(fcm_token='')
    print(f"\n📱 Total vendors with FCM tokens: {vendors_with_fcm.count()}")
    
    if vendors_with_fcm.count() == 0:
        print("❌ NO VENDORS HAVE FCM TOKENS!")
        print("💡 Make sure to:")
        print("   1. Open vendor app")
        print("   2. Login as vendor")
        print("   3. FCM token should auto-register")
    else:
        print("✅ Found vendors with FCM tokens")

if __name__ == "__main__":
    debug_vendor_fcm()