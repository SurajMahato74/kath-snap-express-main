#!/usr/bin/env python
"""
Script to fix missing referral codes for existing vendors
Run this from the backend directory: python fix_referral_codes.py
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.ezeyway.settings')
django.setup()

from backend.ezeyway.accounts.models import CustomUser, VendorProfile

def fix_missing_referral_codes():
    print("🔍 Checking for vendors without referral codes...")
    
    # Find all vendor users without referral codes
    vendor_users_without_codes = CustomUser.objects.filter(
        user_type='vendor',
        referral_code__isnull=True
    )
    
    total_vendors = CustomUser.objects.filter(user_type='vendor').count()
    missing_codes = vendor_users_without_codes.count()
    
    print(f"📊 Total vendors: {total_vendors}")
    print(f"❌ Vendors missing referral codes: {missing_codes}")
    
    if missing_codes == 0:
        print("✅ All vendors already have referral codes!")
        return
    
    print(f"\n🔧 Generating referral codes for {missing_codes} vendors...")
    
    generated_count = 0
    
    for user in vendor_users_without_codes:
        try:
            # Check if they have a vendor profile
            if hasattr(user, 'vendor_profile'):
                referral_code = user.generate_referral_code()
                if referral_code:
                    print(f"✅ Generated referral code '{referral_code}' for vendor: {user.username}")
                    generated_count += 1
                else:
                    print(f"❌ Failed to generate referral code for vendor: {user.username}")
            else:
                print(f"⚠️  Vendor user {user.username} has no vendor profile")
        except Exception as e:
            print(f"❌ Error generating referral code for {user.username}: {str(e)}")
    
    print(f"\n🎉 Successfully generated {generated_count} referral codes!")
    print(f"📈 Progress: {generated_count}/{missing_codes} completed")

if __name__ == "__main__":
    fix_missing_referral_codes()