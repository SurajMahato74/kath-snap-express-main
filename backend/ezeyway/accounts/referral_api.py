from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import CustomUser, VendorProfile

@api_view(['POST'])
@permission_classes([AllowAny])
def validate_referral_code_api(request):
    """Validate if a referral code exists and belongs to an approved vendor"""
    referral_code = request.data.get('referral_code', '').strip().upper()
    
    if not referral_code:
        return Response({
            'valid': False,
            'message': 'Referral code is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Find user with this referral code
        referring_user = CustomUser.objects.get(referral_code=referral_code, user_type='vendor')
        
        # Check if vendor is approved
        try:
            referring_vendor = VendorProfile.objects.get(user=referring_user, is_approved=True)
            return Response({
                'valid': True,
                'message': f'Valid referral code from {referring_vendor.business_name}',
                'vendor_name': referring_vendor.business_name
            })
        except VendorProfile.DoesNotExist:
            return Response({
                'valid': False,
                'message': 'Referral code belongs to an unapproved vendor'
            })
            
    except CustomUser.DoesNotExist:
        return Response({
            'valid': False,
            'message': 'Invalid referral code'
        })