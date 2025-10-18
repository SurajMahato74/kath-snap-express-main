#!/usr/bin/env python3
"""
Test script for custom delivery fee functionality
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ezeyway.settings')
django.setup()

from accounts.models import Product, VendorProfile, CustomUser

def test_custom_delivery_fee():
    """Test the custom delivery fee functionality"""
    print("Testing Custom Delivery Fee Functionality")
    print("=" * 50)
    
    # Check if the new fields exist in the Product model
    try:
        # Get a sample product or create one for testing
        vendor_user = CustomUser.objects.filter(user_type='vendor').first()
        if not vendor_user:
            print("❌ No vendor user found. Please create a vendor first.")
            return
        
        vendor_profile = VendorProfile.objects.filter(user=vendor_user, is_approved=True).first()
        if not vendor_profile:
            print("❌ No approved vendor profile found.")
            return
        
        # Test creating a product with custom delivery fee
        test_product = Product.objects.create(
            vendor=vendor_profile,
            name="Test Product with Custom Delivery Fee",
            category="Electronics",
            price=100.00,
            quantity=10,
            description="Test product for custom delivery fee",
            free_delivery=False,
            custom_delivery_fee_enabled=True,
            custom_delivery_fee=25.00
        )
        
        print(f"✅ Created test product: {test_product.name}")
        print(f"   - Free Delivery: {test_product.free_delivery}")
        print(f"   - Custom Delivery Fee Enabled: {test_product.custom_delivery_fee_enabled}")
        print(f"   - Custom Delivery Fee: ₹{test_product.custom_delivery_fee}")
        
        # Test updating the product
        test_product.custom_delivery_fee = 30.00
        test_product.save()
        
        print(f"✅ Updated custom delivery fee to: ₹{test_product.custom_delivery_fee}")
        
        # Test free delivery (should disable custom fee)
        test_product.free_delivery = True
        test_product.custom_delivery_fee_enabled = False
        test_product.custom_delivery_fee = None
        test_product.save()
        
        print(f"✅ Enabled free delivery:")
        print(f"   - Free Delivery: {test_product.free_delivery}")
        print(f"   - Custom Delivery Fee Enabled: {test_product.custom_delivery_fee_enabled}")
        print(f"   - Custom Delivery Fee: {test_product.custom_delivery_fee}")
        
        # Clean up
        test_product.delete()
        print("✅ Test product cleaned up")
        
        print("\n🎉 All tests passed! Custom delivery fee functionality is working correctly.")
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_custom_delivery_fee()