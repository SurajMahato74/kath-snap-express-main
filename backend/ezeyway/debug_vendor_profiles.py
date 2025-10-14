#!/usr/bin/env python
"""
Debug script to check vendor profiles, documents, and shop images
Run this from the Django project root: python debug_vendor_profiles.py
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ezeyway.settings')
django.setup()

from accounts.models import VendorProfile, VendorDocument, VendorShopImage, CustomUser

def debug_vendor_profiles():
    print("=== VENDOR PROFILES DEBUG ===\n")
    
    # Check total counts
    total_profiles = VendorProfile.objects.count()
    total_documents = VendorDocument.objects.count()
    total_images = VendorShopImage.objects.count()
    
    print(f"Total vendor profiles: {total_profiles}")
    print(f"Total vendor documents: {total_documents}")
    print(f"Total shop images: {total_images}")
    print()
    
    # Check each profile
    for i, profile in enumerate(VendorProfile.objects.all()[:5], 1):  # Limit to first 5
        print(f"--- Profile {i}: {profile.business_name} (ID: {profile.id}) ---")
        print(f"User: {profile.user.username} (ID: {profile.user.id})")
        print(f"Approved: {profile.is_approved}")
        print(f"Active: {profile.is_active}")
        
        # Check documents
        documents = VendorDocument.objects.filter(vendor_profile=profile)
        print(f"Documents: {documents.count()}")
        for doc in documents:
            print(f"  - Doc {doc.id}: {doc.document} (uploaded: {doc.uploaded_at})")
        
        # Check shop images
        images = VendorShopImage.objects.filter(vendor_profile=profile)
        print(f"Shop Images: {images.count()}")
        for img in images:
            print(f"  - Image {img.id}: {img.image} (primary: {img.is_primary}, uploaded: {img.uploaded_at})")
        
        print()
    
    # Check superuser
    superusers = CustomUser.objects.filter(is_superuser=True)
    print(f"Superusers: {superusers.count()}")
    for su in superusers:
        print(f"  - {su.username} (ID: {su.id})")
    print()

if __name__ == "__main__":
    debug_vendor_profiles()