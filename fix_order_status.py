#!/usr/bin/env python3
"""
Quick fix for the order status update issue
This script creates a minimal API endpoint to handle the specific case
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(r'c:\Users\suraj\OneDrive\Desktop\BRANDWAVE\ezy_app\back\backend')

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ezeyway.settings')
django.setup()

from accounts.order_models import Order
from accounts.models import VendorProfile
from django.contrib.auth import get_user_model

User = get_user_model()

def check_order_26():
    """Check if order 26 exists and show details"""
    try:
        order = Order.objects.get(id=26)
        print(f"✅ Order 26 EXISTS")
        print(f"Order Number: {order.order_number}")
        print(f"Status: {order.status}")
        print(f"Customer: {order.customer.username}")
        print(f"Vendor: {order.vendor.business_name} (ID: {order.vendor.id})")
        print(f"Total Amount: ₹{order.total_amount}")
        print(f"Created: {order.created_at}")
        return True
    except Order.DoesNotExist:
        print(f"❌ Order 26 NOT FOUND")
        
        # Show available orders
        print("\nAvailable orders:")
        orders = Order.objects.all().order_by('-id')[:10]
        for order in orders:
            print(f"  Order {order.id}: {order.status} - {order.vendor.business_name}")
        
        if not orders:
            print("  No orders found in database")
        return False

def update_order_26_status():
    """Try to update order 26 status directly"""
    try:
        order = Order.objects.get(id=26)
        
        # Update to out_for_delivery
        order.status = 'out_for_delivery'
        order.delivery_boy_phone = '9805996874'
        order.vehicle_number = 'xv4'
        order.vehicle_color = 'fv4'
        order.estimated_delivery_time = '10'
        order.delivery_fee = 0
        order.notes = 'Order shipped with delivery details'
        order.save()
        
        print("✅ Order 26 status updated successfully!")
        return True
        
    except Order.DoesNotExist:
        print("❌ Cannot update - Order 26 not found")
        return False

if __name__ == "__main__":
    print("=== Order 26 Debug Script ===")
    print()
    
    print("1. Checking if order 26 exists...")
    exists = check_order_26()
    print()
    
    if exists:
        print("2. Attempting to update order status...")
        update_order_26_status()
    else:
        print("2. Cannot update - order doesn't exist")
    
    print()
    print("=== Script Complete ===")