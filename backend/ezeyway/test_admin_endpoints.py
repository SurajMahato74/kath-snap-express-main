#!/usr/bin/env python
"""
Test script to verify admin endpoints exist and are accessible
"""

import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ezeyway.settings')
django.setup()

from django.urls import reverse, resolve
from django.test import RequestFactory
from accounts.api_views import admin_approve_vendor_api, admin_reject_vendor_api

def test_admin_endpoints():
    print("=== TESTING ADMIN ENDPOINTS ===\n")
    
    # Test URL patterns
    try:
        approve_url = reverse('api_admin_approve_vendor', kwargs={'vendor_id': 12})
        print(f"✓ Approve URL: {approve_url}")
    except Exception as e:
        print(f"✗ Approve URL error: {e}")
    
    try:
        reject_url = reverse('api_admin_reject_vendor', kwargs={'vendor_id': 12})
        print(f"✓ Reject URL: {reject_url}")
    except Exception as e:
        print(f"✗ Reject URL error: {e}")
    
    # Test URL resolution
    try:
        resolver = resolve('/admin/vendors/12/approve/')
        print(f"✓ Approve resolver: {resolver.func.__name__}")
    except Exception as e:
        print(f"✗ Approve resolver error: {e}")
    
    try:
        resolver = resolve('/admin/vendors/12/reject/')
        print(f"✓ Reject resolver: {resolver.func.__name__}")
    except Exception as e:
        print(f"✗ Reject resolver error: {e}")
    
    # Test function imports
    print(f"✓ admin_approve_vendor_api function: {admin_approve_vendor_api}")
    print(f"✓ admin_reject_vendor_api function: {admin_reject_vendor_api}")

if __name__ == "__main__":
    test_admin_endpoints()