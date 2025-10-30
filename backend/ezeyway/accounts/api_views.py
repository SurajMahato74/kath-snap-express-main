from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
from django.db.models import Q
from rest_framework.pagination import PageNumberPagination
from django.db import transaction
import math
import logging
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger(__name__)
from .models import CustomUser, VendorProfile, VendorDocument, VendorShopImage, Product, ProductImage, VendorWallet, WalletTransaction, UserFavorite, Cart, CartItem, Category, SubCategory, DeliveryRadius, Slider
from datetime import timedelta
from .complete_onboarding_view import complete_vendor_onboarding
from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer,
    ChangePasswordSerializer, ForgotPasswordSerializer,
    ResetPasswordSerializer, OTPSerializer, VendorProfileSerializer,
    VendorDocumentSerializer, VendorShopImageSerializer, AdminUserCreateSerializer,
    AdminUserUpdateSerializer, UserStatsSerializer, SimpleChangePasswordSerializer,
    ProductSerializer, ProductImageSerializer, VendorWalletSerializer,
    WalletTransactionSerializer, AddMoneySerializer, CustomerProductSerializer,
    UserFavoriteSerializer, CartSerializer, CartItemSerializer, CategorySerializer
)

# Add password setup API for Google OAuth users
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def setup_password_api(request):
    """Allow Google OAuth users to set up password for traditional login"""
    try:
        user = request.user
        new_password = request.data.get('password')
        
        if not new_password:
            return Response({'error': 'Password is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if len(new_password) < 6:
            return Response({'error': 'Password must be at least 6 characters'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Set password for the user
        user.set_password(new_password)
        user.plain_password = new_password  # Store plain password as per existing pattern
        user.save()
        
        # Generate new token
        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)
        
        return Response({
            'success': True,
            'message': 'Password set successfully. You can now login with email and password.',
            'token': token.key
        })
        
    except Exception as e:
        logger.error(f"Password setup error: {str(e)}")
        return Response({'error': 'Failed to set password'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
from .utils import send_otp_email, send_verification_email, send_password_reset_email
from accounts import serializers
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_api(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        otp = user.generate_otp()
        send_otp_email(user, otp)
        return Response({
            'message': 'Registration successful. OTP sent to your email.',
            'user_id': user.id,
            'email': user.email
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_api(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        needs_verification = serializer.validated_data.get('needs_verification', False)

        if needs_verification:
            otp = user.generate_otp()
            send_otp_email(user, otp)
            return Response({
                'needs_verification': True,
                'user_id': user.id,
                'message': 'Email not verified. OTP sent to your email.'
            }, status=status.HTTP_200_OK)

        # Check if vendor profile exists and approval status
        try:
            vendor_profile = VendorProfile.objects.get(user=user)
            profile_exists = True
            is_approved = vendor_profile.is_approved
            is_rejected = vendor_profile.is_rejected
            rejection_reason = vendor_profile.rejection_reason
            rejection_date = vendor_profile.rejection_date
        except VendorProfile.DoesNotExist:
            profile_exists = False
            is_approved = False
            is_rejected = False
            rejection_reason = None
            rejection_date = None

        # Check privacy policy agreement - only show if user has vendor profile or is customer
        needs_privacy_agreement = False
        if (profile_exists or user.user_type == 'customer') and not user.privacy_policy_agreed:
            needs_privacy_agreement = True

        if needs_privacy_agreement:
            return Response({
                'needs_privacy_agreement': True,
                'user_id': user.id,
                'user_type': user.user_type,
                'has_vendor_profile': profile_exists,
                'message': 'Privacy policy agreement required before login.'
            }, status=status.HTTP_200_OK)

        token, created = Token.objects.get_or_create(user=user)

        # Determine available roles - users can be both customer and vendor
        available_roles = ['customer']  # All users can be customers

        # Check if user can be a vendor (has approved profile)
        if profile_exists and is_approved:
            available_roles.append('vendor')

        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
            'available_roles': available_roles,
            'current_role': user.user_type,
            'profile_exists': profile_exists,
            'is_approved': is_approved,
            'is_rejected': is_rejected if is_rejected is not None else False,
            'rejection_reason': rejection_reason,
            'rejection_date': rejection_date.isoformat() if rejection_date else None,
            'message': 'Login successful'
        }, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_api(request):
    try:
        request.user.auth_token.delete()
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
    except:
        return Response({'error': 'Error logging out'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def profile_api(request):
    try:
        user = request.user
        print(f"🔑 Profile API called by user: {user.username}, authenticated: {user.is_authenticated}")

        # Ensure token exists and is valid
        token, created = Token.objects.get_or_create(user=user)
        if created:
            print(f"🔑 Created new token for user: {user.username}")

        # Check if vendor profile exists and approval status
        try:
            vendor_profile = VendorProfile.objects.get(user=user)
            profile_exists = True
            is_approved = vendor_profile.is_approved
        except VendorProfile.DoesNotExist:
            profile_exists = False
            is_approved = False

        # Determine available roles - users can be both customer and vendor
        available_roles = ['customer']  # All users can be customers

        # Check if user can be a vendor (has approved profile)
        if profile_exists and is_approved:
            available_roles.append('vendor')

        # Get user data
        serializer = UserSerializer(user)
        user_data = serializer.data

        # Add available_roles to response
        user_data['available_roles'] = available_roles
        user_data['current_role'] = user.user_type
        user_data['token'] = token.key  # Include token in response

        return Response(user_data)
    except Exception as e:
        print(f"🔑 Profile API error: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def test_api(request):
    return Response({
        'success': True,
        'message': 'API is working',
        'host': request.get_host(),
        'headers': dict(request.headers)
    })

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def health_check(request):
    from django.http import JsonResponse
    return JsonResponse({
        'status': 'ok',
        'message': 'Server is running',
        'timestamp': timezone.now().isoformat()
    })

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def vendor_status_test(request):
    from django.http import JsonResponse
    # Test endpoint to check if vendor status API structure works
    return JsonResponse({
        'success': True,
        'profile_exists': True,
        'is_approved': True,
        'business_name': 'Test Business',
        'is_active': True,
        'message': 'This is a test response'
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def notification_status_api(request):
    # Simple notification status endpoint to replace WebSocket
    return Response({
        'success': True,
        'notifications_enabled': True,
        'unread_count': 0,
        'message': 'Notifications working via HTTP'
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def conversations_api(request):
    # Simple conversations endpoint to replace WebSocket
    return Response({
        'success': True,
        'conversations': [],
        'message': 'Conversations working via HTTP'
    })

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_vendor_status_api(request):
    try:
        vendor_profile = VendorProfile.objects.get(user=request.user, is_approved=True)
        
        # Toggle the status
        vendor_profile.is_active = not vendor_profile.is_active
        vendor_profile.status_override = True
        vendor_profile.status_override_date = timezone.now().date()
        vendor_profile.save()
        
        return Response({
            'success': True,
            'is_active': vendor_profile.is_active,
            'message': f'Status changed to {"Active" if vendor_profile.is_active else "Inactive"}'
        })
    except VendorProfile.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Vendor profile not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def vendor_status_api(request):
    from django.http import JsonResponse
    try:
        vendor_profile = VendorProfile.objects.get(user=request.user, is_approved=True)
        return JsonResponse({
            'success': True,
            'profile_exists': True,
            'is_approved': vendor_profile.is_approved,
            'business_name': vendor_profile.business_name,
            'is_active': vendor_profile.is_active,
            'approval_date': vendor_profile.approval_date.isoformat() if vendor_profile.approval_date else None
        })
    except VendorProfile.DoesNotExist:
        return JsonResponse({
            'success': True,
            'profile_exists': False,
            'is_approved': False,
            'business_name': None,
            'is_active': False,
            'approval_date': None
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'profile_exists': False,
            'is_approved': False
        })

@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def update_profile_api(request):
    serializer = UserSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def upload_profile_picture_api(request):
    if 'profile_picture' not in request.FILES:
        return Response({'error': 'No profile picture provided'}, status=status.HTTP_400_BAD_REQUEST)

    user = request.user
    uploaded_file = request.FILES['profile_picture']

    # Save the file to media directory
    import os
    from django.conf import settings
    from django.core.files.storage import default_storage

    # Create filename
    file_extension = os.path.splitext(uploaded_file.name)[1]
    filename = f"profile_pics/{user.id}_profile{file_extension}"

    # Save file
    file_path = default_storage.save(filename, uploaded_file)

    # Update user profile with file path
    user.profile_picture = file_path
    user.save()

    # Return full URL
    full_url = request.build_absolute_uri(f'/media/{file_path}')

    return Response({
        'message': 'Profile picture updated successfully',
        'profile_picture': full_url
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password_api(request):
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.plain_password = serializer.validated_data['new_password']
        user.save()
        
        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)
        
        return Response({
            'message': 'Password changed successfully',
            'token': token.key
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from .serializers import SimpleChangePasswordSerializer

class SimpleChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SimpleChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        # Update password
        user.set_password(serializer.validated_data['new_password'])
        user.plain_password = serializer.validated_data['new_password']
        user.save()

        # Delete old tokens and generate new one
        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)

        return Response({
            'message': 'Password changed successfully',
            'token': token.key
        }, status=status.HTTP_200_OK)

        
@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def forgot_password_api(request):
    serializer = ForgotPasswordSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        user = CustomUser.objects.get(email=email)
        token = user.generate_password_reset_token()
        send_password_reset_email(user, token)
        
        return Response({'message': 'Password reset link sent to your email'})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def reset_password_api(request):
    serializer = ResetPasswordSerializer(data=request.data)
    if serializer.is_valid():
        token = serializer.validated_data['token']
        password = serializer.validated_data['password']
        
        try:
            user = CustomUser.objects.get(password_reset_token=token)
            
            if user.password_reset_sent_at:
                expiry_time = user.password_reset_sent_at + timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRY_HOURS)
                if timezone.now() > expiry_time:
                    return Response({'error': 'Token expired'}, status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(password)
            user.plain_password = password
            user.password_reset_token = None
            user.save()
            
            return Response({'message': 'Password reset successful'})
            
        except CustomUser.DoesNotExist:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def send_otp_api(request):
    email = request.data.get('email')
    if not email:
        return Response({'error': 'Email required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = CustomUser.objects.get(email=email)
        otp = user.generate_otp()
        send_otp_email(user, otp)
        
        return Response({'message': 'OTP sent successfully'})
    except CustomUser.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def verify_otp_api(request):
    serializer = OTPSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        otp = serializer.validated_data['otp']
        
        try:
            user = CustomUser.objects.get(email=email)
            
            if user.otp_created_at:
                expiry_time = user.otp_created_at + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
                if timezone.now() > expiry_time:
                    return Response({'error': 'OTP expired'}, status=status.HTTP_400_BAD_REQUEST)
            
            if user.email_otp == otp:
                user.email_verified = True
                user.is_verified = True
                user.email_otp = None
                user.phone_otp = None
                user.save()

                # Check if vendor profile exists and approval status
                try:
                    vendor_profile = VendorProfile.objects.get(user=user)
                    profile_exists = True
                    is_approved = vendor_profile.is_approved
                    is_rejected = vendor_profile.is_rejected
                    rejection_reason = vendor_profile.rejection_reason
                    rejection_date = vendor_profile.rejection_date
                except VendorProfile.DoesNotExist:
                    profile_exists = False
                    is_approved = False
                    is_rejected = False
                    rejection_reason = None
                    rejection_date = None

                # Check privacy policy agreement - only show if user has vendor profile or is customer
                needs_privacy_agreement = False
                if (profile_exists or user.user_type == 'customer') and not user.privacy_policy_agreed:
                    needs_privacy_agreement = True

                if needs_privacy_agreement:
                    return Response({
                        'needs_privacy_agreement': True,
                        'user_id': user.id,
                        'user_type': user.user_type,
                        'has_vendor_profile': profile_exists,
                        'message': 'OTP verified. Privacy policy agreement required before login.'
                    })

                token, created = Token.objects.get_or_create(user=user)

                # Determine available roles
                available_roles = ['customer']
                if profile_exists and is_approved:
                    available_roles.append('vendor')

                return Response({
                    'message': 'OTP verified successfully',
                    'token': token.key,
                    'user': UserSerializer(user).data,
                    'available_roles': available_roles,
                    'current_role': user.user_type,
                    'profile_exists': profile_exists,
                    'is_approved': is_approved,
                    'is_rejected': is_rejected,
                    'rejection_reason': rejection_reason,
                    'rejection_date': rejection_date.isoformat() if rejection_date else None
                })
            else:
                return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)
                
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def verify_email_api(request, token):
    try:
        user = CustomUser.objects.get(email_verification_token=token)
        
        if user.email_verification_sent_at:
            expiry_time = user.email_verification_sent_at + timedelta(hours=settings.VERIFICATION_TOKEN_EXPIRY_HOURS)
            if timezone.now() > expiry_time:
                return Response({'error': 'Verification link expired'}, status=status.HTTP_400_BAD_REQUEST)
        
        user.email_verified = True
        user.is_verified = True
        user.email_verification_token = None
        user.save()
        
        return Response({'message': 'Email verified successfully'})
        
    except CustomUser.DoesNotExist:
        return Response({'error': 'Invalid verification link'}, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def update_email_api(request):
    user_id = request.data.get('user_id')
    email = request.data.get('email')
    if not user_id or not email:
        return Response({'error': 'User ID and email required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = CustomUser.objects.get(id=user_id)
        user.email = email
        user.email_verified = False
        user.save()

        token = user.generate_verification_token()
        send_verification_email(user, token)

        return Response({'message': 'Email updated. Verification email sent.'})
    except CustomUser.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def resend_verification_api(request):
    user_id = request.data.get('user_id')
    if not user_id:
        return Response({'error': 'User ID required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = CustomUser.objects.get(id=user_id)
        if user.email_verified:
            return Response({'message': 'Email already verified'})

        token = user.generate_verification_token()
        send_verification_email(user, token)

        return Response({'message': 'Verification email sent'})
    except CustomUser.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

# Vendor API Views
class VendorProfileListCreateView(generics.ListCreateAPIView):
    serializer_class = VendorProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return VendorProfile.objects.all()
        return VendorProfile.objects.filter(user=self.request.user)

    @transaction.atomic
    def perform_create(self, serializer):
        from rest_framework import serializers as drf_serializers
        # Prevent duplicate profiles
        if VendorProfile.objects.filter(user=self.request.user).exists():
            raise drf_serializers.ValidationError({'user': 'Vendor profile already exists.'})
        
        # Auto-set delivery radius from admin settings
        default_radius = DeliveryRadius.objects.first()
        if default_radius:
            serializer.validated_data['delivery_radius'] = default_radius.radius
        
        # Handle referral code
        referral_code = serializer.validated_data.pop('referral_code', None)
        
        # Save vendor profile first
        vendor_profile = serializer.save(user=self.request.user)
        
        # Process referral code if provided
        if referral_code:
            self.process_referral_code(referral_code, vendor_profile)
    
    def process_referral_code(self, referral_code, new_vendor_profile):
        """Process referral code and award points to both vendors"""
        try:
            # Find the referring vendor
            referring_user = CustomUser.objects.get(referral_code=referral_code, user_type='vendor')
            referring_vendor = VendorProfile.objects.get(user=referring_user, is_approved=True)
            
            # Get or create wallets
            new_wallet, _ = VendorWallet.objects.get_or_create(vendor=new_vendor_profile)
            referring_wallet, _ = VendorWallet.objects.get_or_create(vendor=referring_vendor)
            
            # Award 200 points to both vendors
            new_wallet.add_money(200, "Referral bonus - New vendor signup")
            referring_wallet.add_money(200, f"Referral bonus - Referred {new_vendor_profile.business_name}")
            
        except CustomUser.DoesNotExist:
            # Invalid referral code - silently ignore
            pass
        except VendorProfile.DoesNotExist:
            # Referring vendor not approved - silently ignore
            pass

class VendorProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = VendorProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def dispatch(self, request, *args, **kwargs):
        logger.debug(f"VendorProfileDetailView dispatch called with method: {request.method}, path: {request.path}")
        logger.debug(f"URL kwargs: {kwargs}")
        return super().dispatch(request, *args, **kwargs)
    
    def get_object(self):
        pk = self.kwargs.get('pk')
        user = self.request.user
        logger.debug(f"VendorProfileDetailView get_object called by user: {user.username}, is_superuser: {user.is_superuser}, pk: {pk}")
        
        # Check if profile exists at all
        all_profiles = VendorProfile.objects.all().values_list('id', flat=True)
        logger.debug(f"All existing profile IDs: {list(all_profiles)}")
        
        try:
            if user.is_superuser:
                # Superuser can access any profile
                profile = VendorProfile.objects.get(pk=pk)
                logger.debug(f"Superuser found profile: {profile.id} for business: {profile.business_name}")
                return profile
            else:
                # Check if user owns this profile first
                try:
                    profile = VendorProfile.objects.get(pk=pk, user=user)
                    logger.debug(f"User found their own profile: {profile.id}")
                    return profile
                except VendorProfile.DoesNotExist:
                    # If not owner, allow access to approved profiles for public viewing
                    profile = VendorProfile.objects.get(pk=pk, is_approved=True)
                    logger.debug(f"Public access to approved profile: {profile.id} for business: {profile.business_name}")
                    return profile
        except VendorProfile.DoesNotExist:
            logger.error(f"Profile with pk={pk} not found or not accessible. Available IDs: {list(all_profiles)}")
            from rest_framework.exceptions import NotFound
            raise NotFound('Vendor profile not found')
    
    def retrieve(self, request, *args, **kwargs):
        logger.debug(f"VendorProfileDetailView retrieve called with args: {args}, kwargs: {kwargs}")
        logger.debug(f"Request path: {request.path}")
        logger.debug(f"Request method: {request.method}")
        logger.debug(f"Request user: {request.user.username} (authenticated: {request.user.is_authenticated})")
        try:
            instance = self.get_object()
            logger.debug(f"Retrieved profile: {instance.id}, serializing...")
            serializer = self.get_serializer(instance)
            data = serializer.data
            logger.debug(f"Serialized data keys: {list(data.keys())}")
            logger.debug(f"Documents count: {len(data.get('documents', []))}")
            logger.debug(f"Shop images count: {len(data.get('shop_images', []))}")
            return Response(data)
        except Exception as e:
            logger.error(f"Error in VendorProfileDetailView retrieve: {str(e)}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    


class VendorDocumentListCreateView(generics.ListCreateAPIView):
    serializer_class = VendorDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return VendorDocument.objects.all()
        return VendorDocument.objects.filter(vendor_profile__user=self.request.user)

    @transaction.atomic
    def perform_create(self, serializer):
        # Ensure vendor profile exists and belongs to the user
        vendor_profile_id = self.request.data.get('vendor_profile')
        try:
            vendor_profile = VendorProfile.objects.get(id=vendor_profile_id, user=self.request.user)
        except VendorProfile.DoesNotExist:
            from rest_framework import serializers as drf_serializers
            raise drf_serializers.ValidationError({'vendor_profile': 'Invalid vendor profile or access denied.'})
        
        # Handle file upload
        uploaded_file = serializer.validated_data.get('document')
        if uploaded_file:
            import os
            from django.conf import settings
            from django.core.files.storage import default_storage
            
            # Create filename
            file_extension = os.path.splitext(uploaded_file.name)[1]
            filename = f"documents/{vendor_profile.id}_{timezone.now().timestamp()}{file_extension}"
            
            # Save file
            file_path = default_storage.save(filename, uploaded_file)
            # Remove the file from validated_data and add the path
            serializer.validated_data.pop('document')
            serializer.save(vendor_profile=vendor_profile, document=file_path)
        else:
            from rest_framework import serializers as drf_serializers
            raise drf_serializers.ValidationError({'document': 'Document file is required.'})

class VendorShopImageListCreateView(generics.ListCreateAPIView):
    serializer_class = VendorShopImageSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return VendorShopImage.objects.all()
        return VendorShopImage.objects.filter(vendor_profile__user=self.request.user)

    @transaction.atomic
    def perform_create(self, serializer):
        vendor_profile_id = self.request.data.get('vendor_profile')
        try:
            vendor_profile = VendorProfile.objects.get(id=vendor_profile_id, user=self.request.user)
        except VendorProfile.DoesNotExist:
            from rest_framework import serializers as drf_serializers
            raise drf_serializers.ValidationError({'vendor_profile': 'Invalid vendor profile or access denied.'})
        
        # Handle file upload
        uploaded_file = self.request.FILES.get('image')
        if uploaded_file:
            import os
            from django.conf import settings
            from django.core.files.storage import default_storage
            
            # Create filename
            file_extension = os.path.splitext(uploaded_file.name)[1]
            filename = f"shop_images/{vendor_profile.id}_{timezone.now().timestamp()}{file_extension}"
            
            # Save file
            file_path = default_storage.save(filename, uploaded_file)
            serializer.save(vendor_profile=vendor_profile, image=file_path)
        else:
            from rest_framework import serializers as drf_serializers
            raise drf_serializers.ValidationError({'image': 'Image file is required.'})

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def vendor_toggle_status_api(request, pk):
    try:
        # Get the vendor profile
        if request.user.is_superuser:
            vendor_profile = VendorProfile.objects.get(id=pk)
        else:
            # For regular vendors, get their own profile regardless of pk
            vendor_profile = VendorProfile.objects.get(user=request.user)

        # Validate request data
        is_active = request.data.get('is_active')
        if not isinstance(is_active, bool):
            return Response({'error': 'is_active must be a boolean'}, status=status.HTTP_400_BAD_REQUEST)

        # Check wallet balance if trying to go online
        if is_active:
            wallet, created = VendorWallet.objects.get_or_create(vendor=vendor_profile)
            if wallet.balance < 100:
                # Force offline and disable toggle
                vendor_profile.is_active = False
                vendor_profile.status_override = True
                vendor_profile.status_override_date = timezone.now().date()
                vendor_profile.save()
                
                return Response({
                    'error': 'Insufficient wallet balance. Minimum 100 points required to go online.',
                    'wallet_balance': float(wallet.balance),
                    'required_balance': 100,
                    'is_active': False,
                    'can_toggle': False
                }, status=status.HTTP_400_BAD_REQUEST)

        # Update status
        vendor_profile.is_active = is_active
        vendor_profile.status_override = True
        vendor_profile.status_override_date = timezone.now().date()
        vendor_profile.save()

        status_text = 'activated' if is_active else 'deactivated'

        return Response({
            'message': f'Vendor {vendor_profile.business_name} {status_text} successfully',
            'vendor': VendorProfileSerializer(vendor_profile, context={'request': request}).data
        })

    except VendorProfile.DoesNotExist:
        return Response({'error': 'Vendor profile not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# Admin API Views
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def admin_dashboard_api(request):
    if not request.user.is_superuser:
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    total_users = CustomUser.objects.count()
    total_customers = CustomUser.objects.filter(user_type='customer').count()
    total_vendors = CustomUser.objects.filter(user_type='vendor').count()
    pending_vendors = VendorProfile.objects.filter(is_approved=False).count()
    
    return Response({
        'total_users': total_users,
        'total_customers': total_customers,
        'total_vendors': total_vendors,
        'pending_vendors': pending_vendors,
        'recent_users': UserSerializer(CustomUser.objects.order_by('-date_joined')[:10], many=True).data
    })

class UserListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if not self.request.user.is_superuser:
            return CustomUser.objects.none()
        return CustomUser.objects.all().order_by('-date_joined')

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def admin_stats_api(request):
    if not request.user.is_superuser:
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    total_users = CustomUser.objects.count()
    total_customers = CustomUser.objects.filter(user_type='customer').count()
    total_vendors = CustomUser.objects.filter(user_type='vendor').count()
    total_superusers = CustomUser.objects.filter(user_type='superuser').count()
    pending_vendors = VendorProfile.objects.filter(is_approved=False).count()
    verified_users = CustomUser.objects.filter(email_verified=True).count()
    unverified_users = CustomUser.objects.filter(email_verified=False).count()
    
    stats_data = {
        'total_users': total_users,
        'total_customers': total_customers,
        'total_vendors': total_vendors,
        'total_superusers': total_superusers,
        'pending_vendors': pending_vendors,
        'verified_users': verified_users,
        'unverified_users': unverified_users,
    }
    
    serializer = UserStatsSerializer(stats_data)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def admin_create_user_api(request):
    if not request.user.is_superuser:
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    serializer = AdminUserCreateSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({
            'message': 'User created successfully',
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def admin_update_user_api(request, user_id):
    if not request.user.is_superuser:
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = AdminUserUpdateSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({
            'message': 'User updated successfully',
            'user': UserSerializer(user).data
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def admin_delete_user_api(request, user_id):
    if not request.user.is_superuser:
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        user = CustomUser.objects.get(id=user_id)
        if user.is_superuser and CustomUser.objects.filter(user_type='superuser').count() <= 1:
            return Response({'error': 'Cannot delete the last superuser'}, status=status.HTTP_400_BAD_REQUEST)
        
        username = user.username
        user.delete()
        return Response({'message': f'User {username} deleted successfully'})
    except CustomUser.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def admin_toggle_user_status_api(request, user_id):
    if not request.user.is_superuser:
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        user = CustomUser.objects.get(id=user_id)
        user.is_active = not user.is_active
        user.save()
        
        status_text = 'activated' if user.is_active else 'deactivated'
        return Response({
            'message': f'User {user.username} {status_text} successfully',
            'user': UserSerializer(user).data
        })
    except CustomUser.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def admin_approve_vendor_api(request, vendor_id):
    if not request.user.is_superuser:
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        vendor_profile = VendorProfile.objects.get(id=vendor_id)
        vendor_profile.is_approved = True
        vendor_profile.approval_date = timezone.now()
        vendor_profile.is_rejected = False
        vendor_profile.rejection_reason = None
        vendor_profile.rejection_date = None
        vendor_profile.save()
        
        # Send approval email
        from .email_notifications import send_vendor_approval_email
        send_vendor_approval_email(vendor_profile)
        
        return Response({
            'message': f'Vendor {vendor_profile.business_name} approved successfully',
            'vendor': VendorProfileSerializer(vendor_profile, context={'request': request}).data
        })
    except VendorProfile.DoesNotExist:
        return Response({'error': 'Vendor profile not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def admin_reject_vendor_api(request, vendor_id):
    if not request.user.is_superuser:
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

    try:
        vendor_profile = VendorProfile.objects.get(id=vendor_id)
        rejection_reason = request.data.get('reason', '')
        
        vendor_profile.is_rejected = True
        vendor_profile.is_approved = False
        vendor_profile.rejection_reason = rejection_reason
        vendor_profile.rejection_date = timezone.now()
        vendor_profile.save()
        
        # Send rejection email
        from .email_notifications import send_vendor_rejection_email
        send_vendor_rejection_email(vendor_profile)

        return Response({
            'message': f'Vendor "{vendor_profile.business_name}" has been rejected successfully'
        })
    except VendorProfile.DoesNotExist:
        return Response({'error': 'Vendor profile not found'}, status=status.HTTP_404_NOT_FOUND)

# Product API Views
class ProductListCreateView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Product.objects.all().order_by('-created_at')
        try:
            vendor_profile = VendorProfile.objects.get(user=self.request.user)
            return Product.objects.filter(vendor=vendor_profile).order_by('-created_at')
        except VendorProfile.DoesNotExist:
            return Product.objects.none()

    def perform_create(self, serializer):
        try:
            vendor_profile = VendorProfile.objects.get(user=self.request.user)
            serializer.save(vendor=vendor_profile)
        except VendorProfile.DoesNotExist:
            raise serializers.ValidationError({'vendor': 'Vendor profile not found.'})

class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Product.objects.all()
        try:
            vendor_profile = VendorProfile.objects.get(user=self.request.user)
            return Product.objects.filter(vendor=vendor_profile)
        except VendorProfile.DoesNotExist:
            return Product.objects.none()

@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_product_image(request, product_id, image_id):
    try:
        if request.user.is_superuser:
            product = Product.objects.get(id=product_id)
        else:
            vendor_profile = VendorProfile.objects.get(user=request.user)
            product = Product.objects.get(id=product_id, vendor=vendor_profile)
        
        image = ProductImage.objects.get(id=image_id, product=product)
        image.delete()
        
        return Response({'message': 'Image deleted successfully'})
    except (Product.DoesNotExist, ProductImage.DoesNotExist, VendorProfile.DoesNotExist):
        return Response({'error': 'Image not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def set_primary_image(request, product_id, image_id):
    try:
        if request.user.is_superuser:
            product = Product.objects.get(id=product_id)
        else:
            vendor_profile = VendorProfile.objects.get(user=request.user)
            product = Product.objects.get(id=product_id, vendor=vendor_profile)
        
        # Set all images to non-primary
        ProductImage.objects.filter(product=product).update(is_primary=False)
        
        # Set the selected image as primary
        image = ProductImage.objects.get(id=image_id, product=product)
        image.is_primary = True
        image.save()
        
        return Response({'message': 'Primary image set successfully'})
    except (Product.DoesNotExist, ProductImage.DoesNotExist, VendorProfile.DoesNotExist):
        return Response({'error': 'Image not found'}, status=status.HTTP_404_NOT_FOUND)

# Wallet API Views
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def vendor_wallet_api(request):
    try:
        vendor_profile = VendorProfile.objects.get(user=request.user, is_approved=True)
        wallet, created = VendorWallet.objects.get_or_create(vendor=vendor_profile)
        
        serializer = VendorWalletSerializer(wallet, context={'request': request})
        return Response(serializer.data)
    except VendorProfile.DoesNotExist:
        return Response({'error': 'Vendor profile not found or not approved'}, status=status.HTTP_403_FORBIDDEN)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def wallet_transactions_api(request):
    try:
        vendor_profile = VendorProfile.objects.get(user=request.user, is_approved=True)
        wallet = VendorWallet.objects.get(vendor=vendor_profile)
        
        # Get query parameters for filtering
        date_filter = request.GET.get('date_filter', 'all')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        
        transactions = wallet.transactions.all()
        
        # Apply date filtering
        if date_filter == 'today':
            from datetime import date
            transactions = transactions.filter(created_at__date=date.today())
        elif date_filter == 'week':
            from datetime import date, timedelta
            week_ago = date.today() - timedelta(days=7)
            transactions = transactions.filter(created_at__date__gte=week_ago)
        elif date_filter == 'custom':
            date_from = request.GET.get('date_from')
            date_to = request.GET.get('date_to')
            if date_from and date_to:
                transactions = transactions.filter(
                    created_at__date__gte=date_from,
                    created_at__date__lte=date_to
                )
        
        # Pagination
        total_count = transactions.count()
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        transactions = transactions[start_index:end_index]
        
        serializer = WalletTransactionSerializer(transactions, many=True)
        
        return Response({
            'transactions': serializer.data,
            'total_count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size
        })
    except VendorProfile.DoesNotExist:
        return Response({'error': 'Vendor profile not found or not approved'}, status=status.HTTP_403_FORBIDDEN)
    except VendorWallet.DoesNotExist:
        return Response({'error': 'Wallet not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def initiate_khalti_payment(request):
    import requests
    import json
    
    try:
        vendor_profile = VendorProfile.objects.get(user=request.user, is_approved=True)
        amount = float(request.data.get('amount', 0))
        
        if amount <= 0:
            return Response({'error': 'Invalid amount'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Khalti payment initiation
        amount_in_paisa = int(amount * 100)
        return_url = "http://localhost:8080/vendor/wallet?payment_complete=1"
        
        payload = {
            "return_url": return_url,
            "website_url": request.build_absolute_uri('/')[:-1],
            "amount": amount_in_paisa,
            "purchase_order_id": f"Wallet_{vendor_profile.id}_{timezone.now().timestamp()}",
            "purchase_order_name": "Wallet Recharge",
            "customer_info": {
                "name": vendor_profile.owner_name or request.user.username,
                "email": vendor_profile.business_email or request.user.email,
                "phone": vendor_profile.business_phone or "9800000000"
            }
        }
        
        headers = {
            'Authorization': 'key eee666a6159b46a89eda9a4dde2a785b',
            'Content-Type': 'application/json',
        }
        
        response = requests.post(
            'https://a.khalti.com/api/v2/epayment/initiate/',
            data=json.dumps(payload),
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            response_data = response.json()
            if 'pidx' in response_data and 'payment_url' in response_data:
                return Response({
                    'success': True,
                    'payment_url': response_data['payment_url'],
                    'pidx': response_data['pidx']
                })
            else:
                return Response({'error': 'Invalid response from Khalti'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'Failed to initiate payment'}, status=status.HTTP_400_BAD_REQUEST)
            
    except VendorProfile.DoesNotExist:
        return Response({'error': 'Vendor profile not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_money_api(request):
    serializer = AddMoneySerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        vendor_profile = VendorProfile.objects.get(user=request.user, is_approved=True)
        wallet, created = VendorWallet.objects.get_or_create(vendor=vendor_profile)
        
        amount = serializer.validated_data['amount']
        payment_method = serializer.validated_data['payment_method']
        reference_id = serializer.validated_data.get('reference_id', '')
        
        # Add money to wallet
        wallet.add_money(
            amount=amount,
            description=f"Wallet Recharge via {payment_method}"
        )
        
        # Update the transaction with payment details
        latest_transaction = wallet.transactions.first()
        if latest_transaction:
            latest_transaction.payment_method = payment_method
            latest_transaction.reference_id = reference_id
            latest_transaction.save()
        
        return Response({
            'message': 'Money added successfully',
            'new_balance': wallet.balance,
            'transaction_id': latest_transaction.id if latest_transaction else None
        })
    except VendorProfile.DoesNotExist:
        return Response({'error': 'Vendor profile not found'}, status=status.HTTP_404_NOT_FOUND)

# Customer Search Views
class SearchPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50

def calculate_distance(lat1, lon1, lat2, lon2):
    """Google Maps precision Haversine formula with higher precision"""
    # Convert to float with full precision
    lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
    
    R = 6371000  # Earth's radius in meters for higher precision
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    
    a = (math.sin(dlat / 2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * 
         math.sin(dlon / 2) ** 2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return (R * c) / 1000  # Convert back to km

class CustomerProductSearchView(generics.ListAPIView):
    serializer_class = CustomerProductSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = SearchPagination
    
    def get_queryset(self):
        print("\nPRODUCT SEARCH DEBUG - Starting query")
        print(f"Query params: {dict(self.request.query_params)}")
        
        # Get current time and day for vendor availability check
        current_time = timezone.now().time()
        current_day = timezone.now().strftime('%A').lower()
        current_date = timezone.now().date()
        
        # Initial filter with vendor online status
        queryset = Product.objects.filter(
            status='active',
            vendor__is_approved=True
        ).select_related('vendor').prefetch_related('images')
        
        # Filter for online vendors only
        online_vendors = []
        for product in queryset:
            vendor = product.vendor
            
            # Check if vendor has status override for today
            if vendor.status_override and vendor.status_override_date == current_date:
                if vendor.is_active:
                    online_vendors.append(product.id)
                continue
            
            # Check business hours for current day
            day_open = getattr(vendor, f'{current_day}_open')
            day_close = getattr(vendor, f'{current_day}_close')
            day_closed = getattr(vendor, f'{current_day}_closed')
            
            # Vendor is online if not closed and current time is within business hours
            if not day_closed and day_open and day_close and day_open <= current_time < day_close:
                online_vendors.append(product.id)
        
        queryset = queryset.filter(id__in=online_vendors)
        
        initial_count = queryset.count()
        print(f"Initial products (active, approved, online vendors): {initial_count}")
        
        # Search query
        search = self.request.query_params.get('search', '')
        if search:
            print(f"Applying search filter: '{search}'")
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(category__icontains=search) |
                Q(subcategory__icontains=search) |
                Q(tags__icontains=search) |
                Q(vendor__business_name__icontains=search)
            )
            search_count = queryset.count()
            print(f"After search filter: {search_count} products")
        
        # Location-based filtering
        user_lat = self.request.query_params.get('latitude')
        user_lon = self.request.query_params.get('longitude')
        
        if user_lat and user_lon:
            try:
                user_lat = float(user_lat)
                user_lon = float(user_lon)
                print(f"User location: ({user_lat}, {user_lon})")
                
                # Filter products by vendor delivery radius
                filtered_products = []
                total_checked = 0
                within_radius = 0
                
                for product in queryset:
                    vendor = product.vendor
                    total_checked += 1
                    
                    if vendor.latitude and vendor.longitude and vendor.delivery_radius:
                        distance = calculate_distance(
                            user_lat, user_lon,
                            vendor.latitude, vendor.longitude
                        )
                        print(f"Vendor '{vendor.business_name}': distance={distance:.2f}km, radius={vendor.delivery_radius}km")
                        
                        if distance <= vendor.delivery_radius:
                            filtered_products.append(product.id)
                            within_radius += 1
                            print(f"  INCLUDED: Product '{product.name}'")
                        else:
                            print(f"  EXCLUDED: Too far ({distance:.2f}km > {vendor.delivery_radius}km)")
                    else:
                        print(f"Vendor '{vendor.business_name}': Missing location/radius data")
                
                print(f"Location filtering: {within_radius}/{total_checked} products within delivery radius")
                queryset = queryset.filter(id__in=filtered_products)
            except (ValueError, TypeError) as e:
                print(f"Location parsing error: {e}")
        else:
            print("No user location provided - skipping distance filtering")
        
        final_count = queryset.count()
        print(f"Final result: {final_count} products")
        print("PRODUCT SEARCH DEBUG - Complete\n")
        
        return queryset.order_by('-created_at')

class CustomerVendorSearchView(generics.ListAPIView):
    serializer_class = VendorProfileSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = SearchPagination
    
    def get_queryset(self):
        print("\nVENDOR SEARCH DEBUG - Starting query")
        print(f"Query params: {dict(self.request.query_params)}")
        
        # Get current time and day for vendor availability check
        current_time = timezone.now().time()
        current_day = timezone.now().strftime('%A').lower()
        current_date = timezone.now().date()
        
        # Initial filter - only approved vendors
        queryset = VendorProfile.objects.filter(is_approved=True)
        
        # Filter for online vendors only
        online_vendors = []
        for vendor in queryset:
            # Check if vendor has status override for today
            if vendor.status_override and vendor.status_override_date == current_date:
                if vendor.is_active:
                    online_vendors.append(vendor.id)
                continue
            
            # Check business hours for current day
            day_open = getattr(vendor, f'{current_day}_open')
            day_close = getattr(vendor, f'{current_day}_close')
            day_closed = getattr(vendor, f'{current_day}_closed')
            
            # Vendor is online if not closed and current time is within business hours
            if not day_closed and day_open and day_close and day_open <= current_time < day_close:
                online_vendors.append(vendor.id)
        
        queryset = queryset.filter(id__in=online_vendors)
        
        initial_count = queryset.count()
        print(f"Initial vendors (approved & online): {initial_count}")
        
        # Search query
        search = self.request.query_params.get('search', '')
        if search:
            print(f"Applying search filter: '{search}'")
            queryset = queryset.filter(
                Q(business_name__icontains=search) |
                Q(description__icontains=search) |
                Q(business_type__icontains=search) |
                Q(categories__icontains=search)
            )
            search_count = queryset.count()
            print(f"After search filter: {search_count} vendors")
        
        # Location-based filtering
        user_lat = self.request.query_params.get('latitude')
        user_lon = self.request.query_params.get('longitude')
        
        if user_lat and user_lon:
            try:
                user_lat = float(user_lat)
                user_lon = float(user_lon)
                print(f"User location: ({user_lat}, {user_lon})")
                
                # Filter vendors by delivery radius
                filtered_vendors = []
                total_checked = 0
                within_radius = 0
                
                for vendor in queryset:
                    total_checked += 1
                    
                    if vendor.latitude and vendor.longitude and vendor.delivery_radius:
                        distance = calculate_distance(
                            user_lat, user_lon,
                            vendor.latitude, vendor.longitude
                        )
                        print(f"'{vendor.business_name}': distance={distance:.2f}km, radius={vendor.delivery_radius}km")
                        
                        if distance <= vendor.delivery_radius:
                            filtered_vendors.append(vendor.id)
                            within_radius += 1
                            print(f"  INCLUDED: Within delivery range")
                        else:
                            print(f"  EXCLUDED: Too far ({distance:.2f}km > {vendor.delivery_radius}km)")
                    else:
                        print(f"'{vendor.business_name}': Missing location/radius data")
                
                print(f"Location filtering: {within_radius}/{total_checked} vendors within delivery radius")
                queryset = queryset.filter(id__in=filtered_vendors)
            except (ValueError, TypeError) as e:
                print(f"Location parsing error: {e}")
        else:
            print("No user location provided - skipping distance filtering")
        
        final_count = queryset.count()
        print(f"Final result: {final_count} vendors")
        print("VENDOR SEARCH DEBUG - Complete\n")
        
        return queryset.order_by('business_name')

# Customer Vendor Profile View
class CustomerVendorProfileView(generics.RetrieveAPIView):
    serializer_class = VendorProfileSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        return VendorProfile.objects.filter(
            is_approved=True,
            is_active=True
        )
    
    def get_object(self):
        vendor_id = self.kwargs.get('vendor_id')
        try:
            return self.get_queryset().get(id=vendor_id)
        except VendorProfile.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound('Vendor not found or not available')

# Favorite API Views
class UserFavoriteListView(generics.ListAPIView):
    serializer_class = UserFavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Get current time and day for vendor availability check
        current_time = timezone.now().time()
        current_day = timezone.now().strftime('%A').lower()
        current_date = timezone.now().date()
        
        queryset = UserFavorite.objects.filter(user=self.request.user)
        
        # Filter out favorites from offline vendors
        online_favorites = []
        for favorite in queryset:
            vendor = favorite.product.vendor
            is_online = False
            
            # Check if vendor has status override for today
            if vendor.status_override and vendor.status_override_date == current_date:
                is_online = vendor.is_active
            else:
                # Check business hours for current day
                day_open = getattr(vendor, f'{current_day}_open')
                day_close = getattr(vendor, f'{current_day}_close')
                day_closed = getattr(vendor, f'{current_day}_closed')
                
                # Vendor is online if not closed and current time is within business hours
                if not day_closed and day_open and day_close and day_open <= current_time < day_close:
                    is_online = True
            
            if is_online:
                online_favorites.append(favorite.id)
        
        return queryset.filter(id__in=online_favorites)

@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_favorite_api(request):
    product_id = request.data.get('product_id')
    if not product_id:
        return Response({'error': 'Product ID is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        product = Product.objects.get(id=product_id)
        favorite, created = UserFavorite.objects.get_or_create(
            user=request.user,
            product=product
        )
        
        if not created:
            favorite.delete()
            return Response({
                'is_favorite': False,
                'message': 'Product removed from favorites'
            })
        else:
            return Response({
                'is_favorite': True,
                'message': 'Product added to favorites'
            })
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    if not product_id:
        return Response({'error': 'Product ID is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        product = Product.objects.get(id=product_id)
        favorite, created = UserFavorite.objects.get_or_create(
            user=request.user,
            product=product
        )
        
        if not created:
            favorite.delete()
            return Response({
                'is_favorite': False,
                'message': 'Product removed from favorites'
            })
        else:
            return Response({
                'is_favorite': True,
                'message': 'Product added to favorites'
            })
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

# Cart API Views
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_cart_api(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    # Filter out items from offline vendors
    current_time = timezone.now().time()
    current_day = timezone.now().strftime('%A').lower()
    current_date = timezone.now().date()
    
    offline_items = []
    for item in cart.items.all():
        vendor = item.product.vendor
        is_online = False
        
        # Check if vendor has status override for today
        if vendor.status_override and vendor.status_override_date == current_date:
            is_online = vendor.is_active
        else:
            # Check business hours for current day
            day_open = getattr(vendor, f'{current_day}_open')
            day_close = getattr(vendor, f'{current_day}_close')
            day_closed = getattr(vendor, f'{current_day}_closed')
            
            # Vendor is online if not closed and current time is within business hours
            if not day_closed and day_open and day_close and day_open <= current_time < day_close:
                is_online = True
        
        if not is_online:
            offline_items.append(item.id)
    
    # Remove offline vendor items from cart
    if offline_items:
        CartItem.objects.filter(id__in=offline_items).delete()
    
    serializer = CartSerializer(cart, context={'request': request})
    return Response(serializer.data)

@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_to_cart_api(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    
    product_id = request.data.get('product_id')
    quantity = request.data.get('quantity', 1)
    
    if not product_id:
        return Response({'error': 'Product ID is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        product = Product.objects.get(id=product_id, status='active')
        
        # Check if item already exists in cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            # Update quantity if item already exists
            cart_item.quantity += quantity
            cart_item.save()
        
        return Response({
            'message': 'Product added to cart successfully',
            'cart': CartSerializer(cart, context={'request': request}).data
        })
    except Product.DoesNotExist:
        return Response({'error': 'Product not found or inactive'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def update_cart_item_api(request, item_id):
    try:
        cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
        quantity = request.data.get('quantity')
        
        if quantity is None:
            return Response({'error': 'Quantity is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if quantity <= 0:
            cart_item.delete()
            return Response({'message': 'Item removed from cart'})
        
        cart_item.quantity = quantity
        cart_item.save()
        
        return Response({
            'message': 'Cart item updated successfully',
            'cart': CartSerializer(cart_item.cart, context={'request': request}).data
        })
    except CartItem.DoesNotExist:
        return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def remove_from_cart_api(request, item_id):
    try:
        cart_item = CartItem.objects.get(id=item_id, cart__user=request.user)
        cart_item.delete()
        
        cart = Cart.objects.get(user=request.user)
        return Response({
            'message': 'Item removed from cart successfully',
            'cart': CartSerializer(cart, context={'request': request}).data
        })
    except CartItem.DoesNotExist:
        return Response({'error': 'Cart item not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def clear_cart_api(request):
    try:
        cart = Cart.objects.get(user=request.user)
        cart.items.all().delete()
        return Response({'message': 'Cart cleared successfully'})
    except Cart.DoesNotExist:
        return Response({'message': 'Cart is already empty'})

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_categories_api(request):
    categories = Category.objects.filter(is_active=True).order_by('display_order', 'name')
    serializer = CategorySerializer(categories, many=True, context={'request': request})
    return Response({
        'categories': serializer.data
    })

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_subcategories_api(request, category_name):
    try:
        category = Category.objects.get(name=category_name, is_active=True)
        subcategories = category.subcategories.filter(is_active=True).order_by('display_order', 'name')
        subcategory_names = [sub.name for sub in subcategories]
        return Response({
            'subcategories': subcategory_names
        })
    except Category.DoesNotExist:
        return Response({
            'subcategories': []
        })

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_category_parameters_api(request, category_id):
    """Get parameters for a specific category"""
    try:
        category = Category.objects.get(id=category_id, is_active=True)
        parameters = CategoryParameter.objects.filter(category=category)
        
        parameters_data = []
        for param in parameters:
            param_data = {
                'id': param.id,
                'name': param.name,
                'label': param.label,
                'field_type': param.field_type,
                'is_required': param.is_required,
                'description': param.description,
                'placeholder': param.placeholder,
                'min_value': param.min_value,
                'max_value': param.max_value,
                'step': param.step,
                'options': param.options.split(',') if param.options else []
            }
            parameters_data.append(param_data)
            
        return Response({
            'success': True,
            'parameters': parameters_data
        })
    except Category.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Category not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_delivery_radius_api(request):
    # Get the first (smallest) delivery radius as default
    radius = DeliveryRadius.objects.first()
    return Response({
        'delivery_radius': radius.radius if radius else 5.0
    })

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def switch_role_api(request):
    new_role = request.data.get('role')

    if new_role not in ['customer', 'vendor']:
        return Response({'error': 'Invalid role'}, status=status.HTTP_400_BAD_REQUEST)

    user = request.user

    # Check if user can switch to vendor role
    if new_role == 'vendor':
        try:
            vendor_profile = VendorProfile.objects.get(user=user)
            if not vendor_profile.is_approved:
                return Response({'error': 'Vendor profile not approved'}, status=status.HTTP_400_BAD_REQUEST)
        except VendorProfile.DoesNotExist:
            return Response({'error': 'Vendor role not available'}, status=status.HTTP_400_BAD_REQUEST)

    # Update user type using database update to avoid property conflicts
    CustomUser.objects.filter(id=user.id).update(user_type=new_role)
    user.refresh_from_db()

    # Get updated available roles
    available_roles = ['customer']
    if new_role == 'vendor' or VendorProfile.objects.filter(user=user, is_approved=True).exists():
        available_roles.append('vendor')

    return Response({
        'message': f'Switched to {new_role}',
        'current_role': new_role,
        'available_roles': available_roles,
        'user': UserSerializer(user).data
    })

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def verify_khalti_payment(request):
    import requests
    import json
    
    try:
        pidx = request.data.get('pidx')
        if not pidx:
            return Response({'error': 'Payment ID (pidx) is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify payment with Khalti
        headers = {
            'Authorization': 'key eee666a6159b46a89eda9a4dde2a785b',
            'Content-Type': 'application/json',
        }
        
        response = requests.post(
            'https://a.khalti.com/api/v2/epayment/lookup/',
            data=json.dumps({'pidx': pidx}),
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            payment_data = response.json()
            
            if payment_data.get('status') == 'Completed':
                vendor_profile = VendorProfile.objects.get(user=request.user, is_approved=True)
                wallet, created = VendorWallet.objects.get_or_create(vendor=vendor_profile)
                
                from decimal import Decimal
                amount = Decimal(str(payment_data.get('total_amount', 0))) / 100  # Convert from paisa
                
                # Check if transaction already exists
                existing_transaction = WalletTransaction.objects.filter(
                    wallet=wallet,
                    reference_id=pidx
                ).first()
                
                if not existing_transaction:
                    # Add money to wallet
                    wallet.add_money(
                        amount=amount,
                        description=f"Khalti Payment - {pidx}"
                    )
                    
                    # Update transaction with payment details
                    latest_transaction = wallet.transactions.first()
                    if latest_transaction:
                        latest_transaction.payment_method = 'khalti'
                        latest_transaction.reference_id = pidx
                        latest_transaction.status = 'completed'
                        latest_transaction.save()
                    
                    return Response({
                        'success': True,
                        'message': 'Payment verified and wallet updated',
                        'amount': amount,
                        'new_balance': wallet.balance
                    })
                else:
                    return Response({
                        'success': True,
                        'message': 'Payment already processed',
                        'new_balance': wallet.balance
                    })
            else:
                return Response({'error': 'Payment not completed'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'Payment verification failed'}, status=status.HTTP_400_BAD_REQUEST)
            
    except VendorProfile.DoesNotExist:
        return Response({'error': 'Vendor profile not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# Slider API Views
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def register_fcm_token_api(request):
    """Register FCM token for push notifications"""
    try:
        fcm_token = request.data.get('fcm_token')
        platform = request.data.get('platform', 'android')
        
        if not fcm_token:
            return Response({'error': 'FCM token is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Update vendor profile with FCM token
        try:
            vendor_profile = VendorProfile.objects.get(user=request.user, is_approved=True)
            vendor_profile.fcm_token = fcm_token
            vendor_profile.fcm_updated_at = timezone.now()
            vendor_profile.save()
            
            return Response({
                'success': True,
                'message': 'FCM token registered successfully',
                'platform': platform
            })
        except VendorProfile.DoesNotExist:
            # For customers, you can store FCM token in user profile or separate model
            return Response({
                'success': True,
                'message': 'FCM token registered for customer',
                'platform': platform
            })
            
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def test_fcm_notification_api(request):
    """Send test FCM notification to current vendor"""
    try:
        vendor_profile = VendorProfile.objects.get(user=request.user, is_approved=True)
        
        if not vendor_profile.fcm_token:
            return Response({
                'error': 'No FCM token found. Please restart the app.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get test data from request
        title = request.data.get('title', 'Test Notification')
        message = request.data.get('message', 'This is a test notification!')
        order_id = request.data.get('orderId', 999)
        order_number = request.data.get('orderNumber', 'TEST-999')
        amount = request.data.get('amount', '500')
        
        # Send FCM notification
        from .firebase_init import send_data_only_message
        success = send_data_only_message(
            token=vendor_profile.fcm_token,
            data={
                "autoOpen": "true",
                "orderId": str(order_id),
                "orderNumber": order_number,
                "amount": str(amount),
                "action": "autoOpenOrder",
                "forceOpen": "true"
            }
        )
        
        if success:
            return Response({
                'success': True,
                'message': 'Test notification sent successfully!'
            })
        else:
            return Response({
                'error': 'Failed to send notification'
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except VendorProfile.DoesNotExist:
        return Response({
            'error': 'Vendor profile not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_featured_packages_api(request):
    """Get all active featured product packages"""
    from .models import FeaturedProductPackage
    
    packages = FeaturedProductPackage.objects.filter(is_active=True).order_by('duration_days', 'amount')
    
    packages_data = []
    for package in packages:
        package_data = {
            'id': package.id,
            'name': package.name,
            'duration_days': package.duration_days,
            'amount': float(package.amount),
            'package_type': package.package_type,
            'description': package.description,
        }
        packages_data.append(package_data)
    
    return Response({
        'success': True,
        'packages': packages_data
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_product_featured_info_api(request, product_id):
    """Get featured package info for a product"""
    from .models import Product, ProductFeaturedPurchase, VendorProfile
    from datetime import date
    
    try:
        vendor_profile = VendorProfile.objects.get(user=request.user)
        product = Product.objects.get(id=product_id, vendor=vendor_profile)
        
        # Get active featured purchase
        featured_purchase = ProductFeaturedPurchase.objects.filter(
            product=product,
            is_active=True
        ).first()
        
        if not featured_purchase:
            return Response({
                'has_featured': False,
                'can_modify': True
            })
        
        today = date.today()
        can_modify = featured_purchase.start_date > today  # Can modify if not started yet
        
        return Response({
            'has_featured': True,
            'can_modify': can_modify,
            'start_date': featured_purchase.start_date.isoformat(),
            'end_date': featured_purchase.end_date.isoformat(),
            'package_name': featured_purchase.package.name,
            'is_active': featured_purchase.start_date <= today <= featured_purchase.end_date
        })
        
    except (VendorProfile.DoesNotExist, Product.DoesNotExist):
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def reschedule_featured_package_api(request, product_id):
    """Reschedule featured package start date (no wallet charge)"""
    from .models import Product, ProductFeaturedPurchase, VendorProfile
    from datetime import datetime, timedelta
    
    try:
        start_date_str = request.data.get('start_date')
        
        if not start_date_str:
            return Response({'error': 'Start date is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get vendor profile and product
        vendor_profile = VendorProfile.objects.get(user=request.user)
        product = Product.objects.get(id=product_id, vendor=vendor_profile)
        
        # Get active featured purchase
        featured_purchase = ProductFeaturedPurchase.objects.filter(
            product=product,
            is_active=True
        ).first()
        
        if not featured_purchase:
            return Response({'error': 'No active featured package found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Parse new start date
        new_start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        
        # Calculate new end date based on package duration
        duration_days = (featured_purchase.end_date - featured_purchase.start_date).days
        new_end_date = new_start_date + timedelta(days=duration_days)
        
        # Update dates
        featured_purchase.start_date = new_start_date
        featured_purchase.end_date = new_end_date
        featured_purchase.save()
        
        return Response({
            'success': True,
            'message': 'Featured package rescheduled successfully',
            'start_date': new_start_date.isoformat(),
            'end_date': new_end_date.isoformat()
        })
        
    except VendorProfile.DoesNotExist:
        return Response({'error': 'Vendor profile not found'}, status=status.HTTP_404_NOT_FOUND)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    except ValueError:
        return Response({'error': 'Invalid date format'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def purchase_featured_package_api(request):
    """Purchase a featured package for a product"""
    from .models import Product, FeaturedProductPackage, ProductFeaturedPurchase, VendorProfile, VendorWallet
    from datetime import datetime, timedelta
    
    try:
        product_id = request.data.get('product_id')
        package_id = request.data.get('package_id')
        start_date_str = request.data.get('start_date')
        
        if not all([product_id, package_id, start_date_str]):
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get vendor profile
        vendor_profile = VendorProfile.objects.get(user=request.user)
        
        # Get product and package
        product = Product.objects.get(id=product_id, vendor=vendor_profile)
        package = FeaturedProductPackage.objects.get(id=package_id, is_active=True)
        
        # Parse start date
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = start_date + timedelta(days=package.duration_days)
        
        # Get vendor wallet
        wallet, created = VendorWallet.objects.get_or_create(vendor=vendor_profile)
        
        # Check wallet balance
        if wallet.balance < package.amount:
            return Response({
                'error': 'Insufficient wallet balance',
                'required': float(package.amount),
                'available': float(wallet.balance)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Deduct amount from wallet
        success = wallet.deduct_commission(
            amount=package.amount,
            order_amount=package.amount,
            description=f"Featured Package: {package.name} for {product.name}"
        )
        
        if not success:
            return Response({'error': 'Failed to deduct amount from wallet'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create featured purchase record
        featured_purchase = ProductFeaturedPurchase.objects.create(
            product=product,
            vendor=vendor_profile,
            package=package,
            amount_paid=package.amount,
            start_date=start_date,
            end_date=end_date
        )
        
        # Mark product as featured
        product.featured = True
        product.save()
        
        return Response({
            'success': True,
            'message': 'Featured package purchased successfully',
            'purchase_id': featured_purchase.id,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'amount_paid': float(package.amount),
            'new_wallet_balance': float(wallet.balance)
        })
        
    except VendorProfile.DoesNotExist:
        return Response({'error': 'Vendor profile not found'}, status=status.HTTP_404_NOT_FOUND)
    except Product.DoesNotExist:
        return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)
    except FeaturedProductPackage.DoesNotExist:
        return Response({'error': 'Package not found'}, status=status.HTTP_404_NOT_FOUND)
    except ValueError:
        return Response({'error': 'Invalid date format'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_sliders_api(request):
    """Get sliders based on user type and current date/time"""
    from .models import Slider
    
    # Get user type from request (authenticated users) or query param
    user_type = None
    if request.user.is_authenticated:
        user_type = request.user.user_type
    else:
        # For non-authenticated users, default to customer
        user_type = 'customer'
    
    # Allow override via query parameter for testing
    requested_type = request.GET.get('user_type')
    if requested_type in ['customer', 'vendor']:
        user_type = requested_type
    
    # Get current time for date filtering
    now = timezone.now()
    
    # Filter by date range only
    queryset = Slider.objects.filter(
        Q(start_date__isnull=True) | Q(start_date__lte=now)
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=now)
    )
    
    # Order by display order and creation date
    queryset = queryset.order_by('display_order', 'created_at')
    
    # Serialize the data
    sliders_data = []
    for slider in queryset:
        slider_data = {
            'id': slider.id,
            'title': slider.title,
            'description': slider.description,
            'image_url': request.build_absolute_uri(slider.image.url) if slider.image else None,
            'link_url': slider.link_url,
            'visibility': slider.visibility,
            'display_order': slider.display_order,
            'start_date': slider.start_date.isoformat() if slider.start_date else None,
            'end_date': slider.end_date.isoformat() if slider.end_date else None,
            'created_at': slider.created_at.isoformat()
        }
        sliders_data.append(slider_data)
    
    return Response({
        'success': True,
        'sliders': sliders_data,
        'user_type': user_type,
        'count': len(sliders_data)
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def vendor_notifications_api(request):
    """Get vendor notifications (orders, refunds, stock alerts, status changes)"""
    try:
        vendor_profile = VendorProfile.objects.get(user=request.user, is_approved=True)
        
        # Return empty notifications - real notifications will be created by actual events
        notifications = []
        
        return Response({
            'success': True,
            'results': notifications
        })
        
    except VendorProfile.DoesNotExist:
        return Response({'error': 'Vendor profile not found or not approved'}, status=status.HTTP_403_FORBIDDEN)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def facebook_oauth_api(request):
    """Handle Facebook OAuth authentication - follows existing login flow completely"""
    try:
        import json
        
        data = json.loads(request.body)
        user_info = data.get('user_info')
        
        if not user_info:
            return Response({'error': 'Facebook user info required'}, status=status.HTTP_400_BAD_REQUEST)
        
        facebook_id = user_info.get('facebook_id')
        email = user_info.get('email')
        name = user_info.get('name', '')
        picture = user_info.get('picture', '')
        
        logger.info(f"Processing Facebook OAuth for user: {email}")
        
        if not email or not facebook_id:
            return Response({'error': 'Missing required Facebook user data'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user exists by email or facebook_id
        user_created = False
        user = None
        
        # First try to find by facebook_id
        if facebook_id:
            try:
                user = CustomUser.objects.get(facebook_id=facebook_id)
            except CustomUser.DoesNotExist:
                pass
        
        # If not found by facebook_id, try by email
        if not user:
            try:
                user = CustomUser.objects.get(email=email)
                # Link Facebook account to existing user
                if not user.facebook_id:
                    user.facebook_id = facebook_id
                    user.save()
            except CustomUser.DoesNotExist:
                pass
        
        # Create new user if not found
        if not user:
            # Generate unique username from email
            username = email.split('@')[0]
            counter = 1
            original_username = username
            while CustomUser.objects.filter(username=username).exists():
                username = f"{original_username}{counter}"
                counter += 1
            
            # Create user following exact registration flow
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=None,  # No password initially - user can set later
                first_name=name.split(' ')[0] if name else '',
                last_name=' '.join(name.split(' ')[1:]) if len(name.split(' ')) > 1 else '',
                facebook_id=facebook_id,
                profile_picture_url=picture,
                email_verified=True,  # Facebook emails are verified
                is_verified=True,
                user_type='customer'  # Default to customer
            )
            # Set database fields directly after creation to avoid property conflicts
            CustomUser.objects.filter(id=user.id).update(is_customer=True, is_vendor=False)
            user.refresh_from_db()
            user_created = True
            logger.info(f"Created new Facebook OAuth user: {user.email}")
        else:
            # Update existing user info
            updated = False
            if picture and user.profile_picture_url != picture:
                user.profile_picture_url = picture
                updated = True
            if not user.first_name and name:
                user.first_name = name.split(' ')[0]
                user.last_name = ' '.join(name.split(' ')[1:]) if len(name.split(' ')) > 1 else ''
                updated = True
            if not user.email_verified:
                user.email_verified = True
                user.is_verified = True
                updated = True
            if updated:
                user.save()
                logger.info(f"Updated existing Facebook OAuth user: {user.email}")
        
        # Generate or get auth token (same as login flow)
        token, created = Token.objects.get_or_create(user=user)
        
        # Check vendor profile status (EXACT same logic as login_api)
        try:
            vendor_profile = VendorProfile.objects.get(user=user)
            profile_exists = True
            is_approved = vendor_profile.is_approved
            is_rejected = vendor_profile.is_rejected
            rejection_reason = vendor_profile.rejection_reason
            rejection_date = vendor_profile.rejection_date
        except VendorProfile.DoesNotExist:
            profile_exists = False
            is_approved = False
            is_rejected = False
            rejection_reason = None
            rejection_date = None
        
        # Check privacy policy agreement - only show if user has vendor profile or is customer
        needs_privacy_agreement = False
        if (profile_exists or user.user_type == 'customer') and not user.privacy_policy_agreed:
            needs_privacy_agreement = True

        if needs_privacy_agreement:
            return Response({
                'needs_privacy_agreement': True,
                'user_id': user.id,
                'user_type': user.user_type,
                'has_vendor_profile': profile_exists,
                'user_created': user_created,
                'facebook_login': True,
                'message': 'Privacy policy agreement required before login.'
            })
        
        # Determine available roles (EXACT same logic as login_api)
        available_roles = ['customer']  # All users can be customers
        
        # Check if user can be a vendor (has approved profile)
        if profile_exists and is_approved:
            available_roles.append('vendor')
        
        # Get user serialized data and add available_roles to it
        user_data = UserSerializer(user).data
        user_data['available_roles'] = available_roles
        
        # Return EXACT same structure as login_api
        return Response({
            'success': True,
            'token': token.key,
            'user': user_data,
            'available_roles': available_roles,
            'current_role': user.user_type,
            'profile_exists': profile_exists,
            'is_approved': is_approved,
            'is_rejected': is_rejected if is_rejected is not None else False,
            'rejection_reason': rejection_reason,
            'rejection_date': rejection_date.isoformat() if rejection_date else None,
            'message': 'Facebook OAuth login successful',
            'user_created': user_created,  # Additional flag for new users
            'needs_password_setup': not user.has_usable_password(),  # Flag for password setup
            'facebook_login': True,  # Flag to indicate Facebook login
            'needs_profile_completion': user_created or not user.phone_number  # Flag for profile completion
        })
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return Response({'error': 'Invalid JSON data'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Facebook OAuth error: {str(e)}")
        import traceback
        logger.error(f"Facebook OAuth traceback: {traceback.format_exc()}")
        return Response({'error': f'Authentication failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@csrf_exempt
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def google_oauth_api(request):
    """Handle Google OAuth authentication - follows existing login flow completely"""
    try:
        import json
        
        data = json.loads(request.body)
        user_info = data.get('user_info')
        
        if not user_info:
            return Response({'error': 'Google user info required'}, status=status.HTTP_400_BAD_REQUEST)
        
        google_id = user_info.get('google_id')
        email = user_info.get('email')
        name = user_info.get('name', '')
        picture = user_info.get('picture', '')
        
        logger.info(f"Processing Google OAuth for user: {email}")
        
        if not email or not google_id:
            return Response({'error': 'Missing required Google user data'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user exists by email or google_id
        user_created = False
        user = None
        
        # First try to find by google_id
        if google_id:
            try:
                user = CustomUser.objects.get(google_id=google_id)
            except CustomUser.DoesNotExist:
                pass
        
        # If not found by google_id, try by email
        if not user:
            try:
                user = CustomUser.objects.get(email=email)
                # Link Google account to existing user
                if not user.google_id:
                    user.google_id = google_id
                    user.save()
            except CustomUser.DoesNotExist:
                pass
        
        # Create new user if not found
        if not user:
            # Generate unique username from email
            username = email.split('@')[0]
            counter = 1
            original_username = username
            while CustomUser.objects.filter(username=username).exists():
                username = f"{original_username}{counter}"
                counter += 1
            
            # Create user following exact registration flow
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=None,  # No password initially - user can set later
                first_name=name.split(' ')[0] if name else '',
                last_name=' '.join(name.split(' ')[1:]) if len(name.split(' ')) > 1 else '',
                google_id=google_id,
                profile_picture_url=picture,
                email_verified=True,  # Google emails are verified
                is_verified=True,
                user_type='customer'  # Default to customer
            )
            # Set database fields directly after creation to avoid property conflicts
            CustomUser.objects.filter(id=user.id).update(is_customer=True, is_vendor=False)
            user.refresh_from_db()
            user_created = True
            logger.info(f"Created new Google OAuth user: {user.email}")
        else:
            # Update existing user info
            updated = False
            if picture and user.profile_picture_url != picture:
                user.profile_picture_url = picture
                updated = True
            if not user.first_name and name:
                user.first_name = name.split(' ')[0]
                user.last_name = ' '.join(name.split(' ')[1:]) if len(name.split(' ')) > 1 else ''
                updated = True
            if not user.email_verified:
                user.email_verified = True
                user.is_verified = True
                updated = True
            if updated:
                user.save()
                logger.info(f"Updated existing Google OAuth user: {user.email}")
        
        # Generate or get auth token (same as login flow)
        token, created = Token.objects.get_or_create(user=user)
        
        # Check vendor profile status (EXACT same logic as login_api)
        try:
            vendor_profile = VendorProfile.objects.get(user=user)
            profile_exists = True
            is_approved = vendor_profile.is_approved
            is_rejected = vendor_profile.is_rejected
            rejection_reason = vendor_profile.rejection_reason
            rejection_date = vendor_profile.rejection_date
        except VendorProfile.DoesNotExist:
            profile_exists = False
            is_approved = False
            is_rejected = False
            rejection_reason = None
            rejection_date = None
        
        # Check privacy policy agreement - only show if user has vendor profile or is customer
        needs_privacy_agreement = False
        if (profile_exists or user.user_type == 'customer') and not user.privacy_policy_agreed:
            needs_privacy_agreement = True

        if needs_privacy_agreement:
            return Response({
                'needs_privacy_agreement': True,
                'user_id': user.id,
                'user_type': user.user_type,
                'has_vendor_profile': profile_exists,
                'user_created': user_created,
                'google_login': True,
                'message': 'Privacy policy agreement required before login.'
            })
        
        # Determine available roles (EXACT same logic as login_api)
        available_roles = ['customer']  # All users can be customers
        
        # Check if user can be a vendor (has approved profile)
        if profile_exists and is_approved:
            available_roles.append('vendor')
        
        # Note: We don't update is_vendor/is_customer database fields here
        # because they conflict with computed properties in the model
        # The role logic is handled by available_roles and user_type
        
        # Get user serialized data and add available_roles to it
        user_data = UserSerializer(user).data
        user_data['available_roles'] = available_roles
        
        # Return EXACT same structure as login_api
        return Response({
            'success': True,
            'token': token.key,
            'user': user_data,
            'available_roles': available_roles,
            'current_role': user.user_type,
            'profile_exists': profile_exists,
            'is_approved': is_approved,
            'is_rejected': is_rejected if is_rejected is not None else False,
            'rejection_reason': rejection_reason,
            'rejection_date': rejection_date.isoformat() if rejection_date else None,
            'message': 'Google OAuth login successful',
            'user_created': user_created,  # Additional flag for new users
            'needs_password_setup': not user.has_usable_password(),  # Flag for password setup
            'google_login': True,  # Flag to indicate Google login
            'needs_profile_completion': user_created or not user.phone_number  # Flag for profile completion
        })
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return Response({'error': 'Invalid JSON data'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Google OAuth error: {str(e)}")
        import traceback
        logger.error(f"Google OAuth traceback: {traceback.format_exc()}")
        return Response({'error': f'Authentication failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_password_setup_api(request):
    """Check if user needs to set up password (for Google OAuth users)"""
    try:
        user = request.user
        return Response({
            'needs_password_setup': not user.has_usable_password(),
            'has_google_account': bool(user.google_id),
            'email': user.email
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def agree_privacy_policy_api(request):
    """Handle privacy policy agreement and complete login"""
    try:
        user_id = request.data.get('user_id')
        agreed = request.data.get('agreed', False)
        
        if not user_id:
            return Response({'error': 'User ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not agreed:
            return Response({'error': 'Privacy policy agreement is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Update privacy policy agreement
        user.privacy_policy_agreed = True
        user.save()
        
        # Generate token and complete login
        token, created = Token.objects.get_or_create(user=user)
        
        # Check vendor profile status
        try:
            vendor_profile = VendorProfile.objects.get(user=user)
            profile_exists = True
            is_approved = vendor_profile.is_approved
            is_rejected = vendor_profile.is_rejected
            rejection_reason = vendor_profile.rejection_reason
            rejection_date = vendor_profile.rejection_date
        except VendorProfile.DoesNotExist:
            profile_exists = False
            is_approved = False
            is_rejected = False
            rejection_reason = None
            rejection_date = None
        
        # Determine available roles
        available_roles = ['customer']
        if profile_exists and is_approved:
            available_roles.append('vendor')
        
        return Response({
            'success': True,
            'token': token.key,
            'user': UserSerializer(user).data,
            'available_roles': available_roles,
            'current_role': user.user_type,
            'profile_exists': profile_exists,
            'is_approved': is_approved,
            'is_rejected': is_rejected if is_rejected is not None else False,
            'rejection_reason': rejection_reason,
            'rejection_date': rejection_date.isoformat() if rejection_date else None,
            'message': 'Privacy policy agreed and login successful'
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def check_wallet_balance_api(request):
    """Check wallet balance and auto-disable if needed"""
    try:
        if not request.user.is_superuser:
            vendor_profile = VendorProfile.objects.get(user=request.user, is_approved=True)
            wallet, created = VendorWallet.objects.get_or_create(vendor=vendor_profile)
            
            can_be_active = wallet.balance >= 100
            
            # Auto-disable if balance is low and currently active
            if not can_be_active and vendor_profile.is_active:
                vendor_profile.is_active = False
                vendor_profile.status_override = True
                vendor_profile.status_override_date = timezone.now().date()
                vendor_profile.save()
            
            return Response({
                'wallet_balance': float(wallet.balance),
                'can_be_active': can_be_active,
                'is_active': vendor_profile.is_active,
                'required_balance': 100
            })
        else:
            # Admin endpoint to check all vendors
            from .wallet_monitor import check_and_disable_low_balance_vendors
            disabled_count = check_and_disable_low_balance_vendors()
            return Response({
                'message': f'Checked all vendors, disabled {disabled_count} due to low balance'
            })
            
    except VendorProfile.DoesNotExist:
        return Response({'error': 'Vendor profile not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def validate_referral_code_api(request):
    """Validate if a referral code exists and belongs to an approved vendor"""
    referral_code = request.data.get('referral_code', '').strip().upper()
    
    if not referral_code:
        return Response({
            'valid': False,
            'message': 'Referral code is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        referring_user = CustomUser.objects.get(referral_code=referral_code, user_type='vendor')
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

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def generate_referral_code_api(request):
    """Generate referral code for the current vendor user if they don't have one"""
    try:
        user = request.user
        if user.user_type == 'vendor':
            if not user.referral_code:
                referral_code = user.generate_referral_code()
                return Response({
                    'success': True,
                    'referral_code': referral_code,
                    'message': 'Referral code generated successfully'
                })
            else:
                return Response({
                    'success': True,
                    'referral_code': user.referral_code,
                    'message': 'Referral code already exists'
                })
        else:
            return Response({
                'success': False,
                'message': 'Only vendors can have referral codes'
            }, status=status.HTTP_403_FORBIDDEN)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Failed to generate referral code: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Direct order accept/reject functions (backup for URL routing issues)
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def vendor_accept_order_direct(request, order_id):
    """Direct vendor accept order function - backup for routing issues"""
    print(f"🔥 DIRECT VENDOR ACCEPT ORDER CALLED - Order ID: {order_id}, User: {request.user}")
    
    # Import the function from order_views and call it
    from .order_views import vendor_accept_order_api
    return vendor_accept_order_api(request, order_id)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def vendor_reject_order_direct(request, order_id):
    """Direct vendor reject order function - backup for routing issues"""
    print(f"🔥 DIRECT VENDOR REJECT ORDER CALLED - Order ID: {order_id}, User: {request.user}")
    
    # Import the function from order_views and call it
    from .order_views import vendor_reject_order_api
    return vendor_reject_order_api(request, order_id)