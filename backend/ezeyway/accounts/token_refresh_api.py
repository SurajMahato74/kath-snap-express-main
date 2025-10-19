from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from .serializers import UserSerializer
from .models import VendorProfile

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refresh_token_api(request):
    """Refresh user token and return updated user data"""
    try:
        user = request.user
        
        # Delete old token and create new one
        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)
        
        # Get updated user data
        try:
            vendor_profile = VendorProfile.objects.get(user=user)
            profile_exists = True
            is_approved = vendor_profile.is_approved
        except VendorProfile.DoesNotExist:
            profile_exists = False
            is_approved = False

        available_roles = ['customer']
        if profile_exists and is_approved:
            available_roles.append('vendor')

        user_data = UserSerializer(user).data
        user_data['available_roles'] = available_roles
        user_data['current_role'] = user.user_type

        return Response({
            'token': token.key,
            'user': user_data,
            'message': 'Token refreshed successfully'
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)