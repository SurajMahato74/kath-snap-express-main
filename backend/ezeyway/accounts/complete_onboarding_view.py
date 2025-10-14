from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.utils import timezone
from django.core.files.storage import default_storage
import os
import json
from .models import VendorProfile, VendorDocument, VendorShopImage, DeliveryRadius
from .serializers import VendorProfileSerializer
from .email_notifications import send_vendor_submission_email

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
@transaction.atomic
def complete_vendor_onboarding(request):
    """Complete vendor onboarding in a single atomic transaction"""
    
    # Check if profile already exists - if so, update it
    existing_profile = VendorProfile.objects.filter(user=request.user).first()
    is_update = existing_profile is not None
    
    try:
        # Create vendor profile
        profile_data = {
            'business_name': request.data.get('business_name'),
            'owner_name': request.data.get('owner_name'),
            'business_email': request.data.get('business_email'),
            'business_phone': request.data.get('business_phone'),
            'business_address': request.data.get('business_address'),
            'location_address': request.data.get('location_address'),
            'city': request.data.get('city'),
            'state': request.data.get('state'),
            'pincode': request.data.get('pincode'),
            'latitude': float(request.data.get('latitude')) if request.data.get('latitude') else None,
            'longitude': float(request.data.get('longitude')) if request.data.get('longitude') else None,
            'business_type': request.data.get('business_type'),
            'categories': json.loads(request.data.get('categories', '[]')),
            'description': request.data.get('description', ''),
            'account_number': request.data.get('account_number', ''),
            'account_holder_name': request.data.get('account_holder_name', ''),
            'bank_name': request.data.get('bank_name', ''),
            'ifsc_code': request.data.get('ifsc_code', ''),
            'gst_number': request.data.get('gst_number', ''),
            'pan_number': request.data.get('pan_number', ''),
            'delivery_radius': request.data.get('delivery_radius', ''),
            'min_order_amount': request.data.get('min_order_amount', ''),
        }
        
        # Auto-set delivery radius from admin settings
        default_radius = DeliveryRadius.objects.first()
        if default_radius:
            profile_data['delivery_radius'] = default_radius.radius
        
        # Handle business license file
        if 'business_license_file' in request.FILES:
            business_license = request.FILES['business_license_file']
            file_extension = os.path.splitext(business_license.name)[1]
            filename = f"business_license/{request.user.id}_{timezone.now().timestamp()}{file_extension}"
            file_path = default_storage.save(filename, business_license)
            profile_data['business_license_file'] = file_path
        
        # Create or update vendor profile
        if is_update:
            # Update existing profile
            for key, value in profile_data.items():
                if value:  # Only update non-empty values
                    setattr(existing_profile, key, value)
            existing_profile.is_rejected = False  # Reset rejection status
            existing_profile.rejection_reason = None
            existing_profile.rejection_date = None
            existing_profile.save()
            vendor_profile = existing_profile
        else:
            # Create new profile
            vendor_profile = VendorProfile.objects.create(user=request.user, **profile_data)
        
        # Handle documents - only add new ones
        if 'citizenship_front' in request.FILES:
            citizenship_front = request.FILES['citizenship_front']
            file_extension = os.path.splitext(citizenship_front.name)[1]
            filename = f"documents/{vendor_profile.id}_citizenship_front_{timezone.now().timestamp()}{file_extension}"
            file_path = default_storage.save(filename, citizenship_front)
            VendorDocument.objects.create(vendor_profile=vendor_profile, document=file_path)
        
        if 'citizenship_back' in request.FILES:
            citizenship_back = request.FILES['citizenship_back']
            file_extension = os.path.splitext(citizenship_back.name)[1]
            filename = f"documents/{vendor_profile.id}_citizenship_back_{timezone.now().timestamp()}{file_extension}"
            file_path = default_storage.save(filename, citizenship_back)
            VendorDocument.objects.create(vendor_profile=vendor_profile, document=file_path)
        
        # Handle shop images - only add new ones
        for i in range(10):  # Support up to 10 images
            field_name = f'shop_image_{i}'
            if field_name in request.FILES:
                shop_image = request.FILES[field_name]
                file_extension = os.path.splitext(shop_image.name)[1]
                filename = f"shop_images/{vendor_profile.id}_{i}_{timezone.now().timestamp()}{file_extension}"
                file_path = default_storage.save(filename, shop_image)
                VendorShopImage.objects.create(
                    vendor_profile=vendor_profile, 
                    image=file_path,
                    is_primary=False  # Don't override existing primary
                )
        
        # Send submission email
        send_vendor_submission_email(vendor_profile)
        
        # Return success response
        serializer = VendorProfileSerializer(vendor_profile, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK if is_update else status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)