#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ezeyway.settings')
django.setup()

from accounts.models import VendorProfile

def fix_vendor_location():
    """Fix vendor location data to make products visible"""
    try:
        # Get the vendor profile
        vendor = VendorProfile.objects.get(business_name="suraj.admi's Business")
        
        print(f"Found vendor: {vendor.business_name}")
        print(f"Current latitude: {vendor.latitude}")
        print(f"Current longitude: {vendor.longitude}")
        print(f"Current delivery_radius: {vendor.delivery_radius}")
        
        # Set location data (using Kathmandu coordinates as example)
        vendor.latitude = 27.663978765476628
        vendor.longitude = 85.34637340189069
        vendor.delivery_radius = 50.0  # 50km radius
        
        # Also ensure vendor is active and approved
        vendor.is_active = True
        vendor.is_approved = True
        
        vendor.save()
        
        print(f"Updated vendor location:")
        print(f"New latitude: {vendor.latitude}")
        print(f"New longitude: {vendor.longitude}")
        print(f"New delivery_radius: {vendor.delivery_radius}")
        print(f"Is active: {vendor.is_active}")
        print(f"Is approved: {vendor.is_approved}")
        
        print("✅ Vendor location updated successfully!")
        
    except VendorProfile.DoesNotExist:
        print("❌ Vendor not found!")
        # List all vendors
        vendors = VendorProfile.objects.all()
        print("Available vendors:")
        for v in vendors:
            print(f"  - {v.business_name} (ID: {v.id})")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_vendor_location()