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
import math
from .models import CustomUser, VendorProfile, VendorDocument, Product, ProductImage, VendorWallet, WalletTransaction, UserFavorite, Cart, CartItem
from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer,
    ChangePasswordSerializer, ForgotPasswordSerializer,
    ResetPasswordSerializer, OTPSerializer, VendorProfileSerializer,
    VendorDocumentSerializer, AdminUserCreateSerializer,
    AdminUserUpdateSerializer, UserStatsSerializer, SimpleChangePasswordSerializer,
    ProductSerializer, ProductImageSerializer, VendorWalletSerializer,
    WalletTransactionSerializer, AddMoneySerializer, CustomerProductSerializer,
    UserFavoriteSerializer, CartSerializer, CartItemSerializer
)
from .utils import send_otp_email, send_verification_email, send_password_reset_email
from accounts import serializers
from rest_framework.parsers import MultiPartParser, FormParser

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

        token, created = Token.objects.get_or_create(user=user)
        
        # Check if vendor profile exists and approval status
        try:
            vendor_profile = VendorProfile.objects.get(user=user)
            profile_exists = True
            is_approved = vendor_profile.is_approved
        except VendorProfile.DoesNotExist:
            profile_exists = False
            is_approved = False

        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
            'profile_exists': profile_exists,
            'is_approved': is_approved,
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
    serializer = UserSerializer(request.user)
    return Response(serializer.data)

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
        if not request.user.is_vendor:
            return Response({
                'success': False,
                'error': 'Not a vendor account'
            }, status=status.HTTP_403_FORBIDDEN)
        
        vendor_profile = VendorProfile.objects.get(user=request.user)
        
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
        if not request.user.is_vendor:
            return JsonResponse({
                'success': False,
                'error': 'Not a vendor account',
                'profile_exists': False,
                'is_approved': False
            })
        
        vendor_profile = VendorProfile.objects.get(user=request.user)
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

                token, created = Token.objects.get_or_create(user=user)

                # Check if vendor profile exists and approval status
                try:
                    vendor_profile = VendorProfile.objects.get(user=user)
                    profile_exists = True
                    is_approved = vendor_profile.is_approved
                except VendorProfile.DoesNotExist:
                    profile_exists = False
                    is_approved = False

                return Response({
                    'message': 'OTP verified successfully',
                    'token': token.key,
                    'user': UserSerializer(user).data,
                    'profile_exists': profile_exists,
                    'is_approved': is_approved
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
        if self.request.user.is_superadmin:
            return VendorProfile.objects.all()
        return VendorProfile.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        from rest_framework import serializers as drf_serializers
        # Ensure user is a vendor
        if not self.request.user.is_vendor:
            raise drf_serializers.ValidationError({'user': 'Only vendors can create a vendor profile.'})
        # Prevent duplicate profiles
        if VendorProfile.objects.filter(user=self.request.user).exists():
            raise drf_serializers.ValidationError({'user': 'Vendor profile already exists.'})
        serializer.save(user=self.request.user)

class VendorProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = VendorProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        if self.request.user.is_superadmin:
            return VendorProfile.objects.all()
        return VendorProfile.objects.filter(user=self.request.user)
    


class VendorDocumentListCreateView(generics.ListCreateAPIView):
    serializer_class = VendorDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superadmin:
            return VendorDocument.objects.all()
        return VendorDocument.objects.filter(vendor_profile__user=self.request.user)

    def perform_create(self, serializer):
        # Ensure vendor profile exists and belongs to the user
        vendor_profile_id = self.request.data.get('vendor_profile')
        try:
            vendor_profile = VendorProfile.objects.get(id=vendor_profile_id, user=self.request.user)
        except VendorProfile.DoesNotExist:
            from rest_framework import serializers as drf_serializers
            raise drf_serializers.ValidationError({'vendor_profile': 'Invalid vendor profile or access denied.'})
        serializer.save(vendor_profile=vendor_profile)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def vendor_toggle_status_api(request, pk):
    try:
        # Get the vendor profile
        if request.user.is_superadmin:
            vendor_profile = VendorProfile.objects.get(id=pk)
        else:
            vendor_profile = VendorProfile.objects.get(id=pk, user=request.user)

        # Validate request data
        is_active = request.data.get('is_active')
        if not isinstance(is_active, bool):
            return Response({'error': 'is_active must be a boolean'}, status=status.HTTP_400_BAD_REQUEST)

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
    if not request.user.is_superadmin:
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
        if not self.request.user.is_superadmin:
            return CustomUser.objects.none()
        return CustomUser.objects.all().order_by('-date_joined')

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def admin_stats_api(request):
    if not request.user.is_superadmin:
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
    if not request.user.is_superadmin:
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
    if not request.user.is_superadmin:
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
    if not request.user.is_superadmin:
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        user = CustomUser.objects.get(id=user_id)
        if user.is_superadmin and CustomUser.objects.filter(user_type='superuser').count() <= 1:
            return Response({'error': 'Cannot delete the last superuser'}, status=status.HTTP_400_BAD_REQUEST)
        
        username = user.username
        user.delete()
        return Response({'message': f'User {username} deleted successfully'})
    except CustomUser.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def admin_toggle_user_status_api(request, user_id):
    if not request.user.is_superadmin:
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
    if not request.user.is_superadmin:
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        vendor_profile = VendorProfile.objects.get(id=vendor_id)
        vendor_profile.is_approved = True
        vendor_profile.approval_date = timezone.now()
        vendor_profile.save()
        
        return Response({
            'message': f'Vendor {vendor_profile.business_name} approved successfully',
            'vendor': VendorProfileSerializer(vendor_profile).data
        })
    except VendorProfile.DoesNotExist:
        return Response({'error': 'Vendor profile not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def admin_reject_vendor_api(request, vendor_id):
    if not request.user.is_superadmin:
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

    try:
        vendor_profile = VendorProfile.objects.get(id=vendor_id)
        vendor_name = vendor_profile.business_name
        username = vendor_profile.user.username

        # Delete the vendor profile (this will cascade delete related documents)
        vendor_profile.delete()

        return Response({
            'message': f'Vendor "{vendor_name}" ({username}) has been rejected and deleted successfully'
        })
    except VendorProfile.DoesNotExist:
        return Response({'error': 'Vendor profile not found'}, status=status.HTTP_404_NOT_FOUND)

# Product API Views
class ProductListCreateView(generics.ListCreateAPIView):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        if self.request.user.is_superadmin:
            return Product.objects.all()
        try:
            vendor_profile = VendorProfile.objects.get(user=self.request.user)
            return Product.objects.filter(vendor=vendor_profile)
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
        if self.request.user.is_superadmin:
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
        if request.user.is_superadmin:
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
        if request.user.is_superadmin:
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
    if not request.user.is_vendor:
        return Response({'error': 'Access denied. Vendor account required.'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        vendor_profile = VendorProfile.objects.get(user=request.user)
        wallet, created = VendorWallet.objects.get_or_create(vendor=vendor_profile)
        
        serializer = VendorWalletSerializer(wallet, context={'request': request})
        return Response(serializer.data)
    except VendorProfile.DoesNotExist:
        return Response({'error': 'Vendor profile not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def wallet_transactions_api(request):
    if not request.user.is_vendor:
        return Response({'error': 'Access denied. Vendor account required.'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        vendor_profile = VendorProfile.objects.get(user=request.user)
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
    except (VendorProfile.DoesNotExist, VendorWallet.DoesNotExist):
        return Response({'error': 'Wallet not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_money_api(request):
    if not request.user.is_vendor:
        return Response({'error': 'Access denied. Vendor account required.'}, status=status.HTTP_403_FORBIDDEN)
    
    serializer = AddMoneySerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        vendor_profile = VendorProfile.objects.get(user=request.user)
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
        print("\n🔍 PRODUCT SEARCH DEBUG - Starting query")
        print(f"📋 Query params: {dict(self.request.query_params)}")
        
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
        print(f"📦 Initial products (active, approved, online vendors): {initial_count}")
        
        # Search query
        search = self.request.query_params.get('search', '')
        if search:
            print(f"🔎 Applying search filter: '{search}'")
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(category__icontains=search) |
                Q(subcategory__icontains=search) |
                Q(tags__icontains=search) |
                Q(vendor__business_name__icontains=search)
            )
            search_count = queryset.count()
            print(f"📦 After search filter: {search_count} products")
        
        # Location-based filtering
        user_lat = self.request.query_params.get('latitude')
        user_lon = self.request.query_params.get('longitude')
        
        if user_lat and user_lon:
            try:
                user_lat = float(user_lat)
                user_lon = float(user_lon)
                print(f"📍 User location: ({user_lat}, {user_lon})")
                
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
                        print(f"🏪 Vendor '{vendor.business_name}': distance={distance:.2f}km, radius={vendor.delivery_radius}km")
                        
                        if distance <= vendor.delivery_radius:
                            filtered_products.append(product.id)
                            within_radius += 1
                            print(f"  ✅ INCLUDED: Product '{product.name}'")
                        else:
                            print(f"  ❌ EXCLUDED: Too far ({distance:.2f}km > {vendor.delivery_radius}km)")
                    else:
                        print(f"🏪 Vendor '{vendor.business_name}': Missing location/radius data")
                
                print(f"📊 Location filtering: {within_radius}/{total_checked} products within delivery radius")
                queryset = queryset.filter(id__in=filtered_products)
            except (ValueError, TypeError) as e:
                print(f"❌ Location parsing error: {e}")
        else:
            print("📍 No user location provided - skipping distance filtering")
        
        final_count = queryset.count()
        print(f"📦 Final result: {final_count} products")
        print("🔍 PRODUCT SEARCH DEBUG - Complete\n")
        
        return queryset.order_by('-created_at')

class CustomerVendorSearchView(generics.ListAPIView):
    serializer_class = VendorProfileSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = SearchPagination
    
    def get_queryset(self):
        print("\n🏪 VENDOR SEARCH DEBUG - Starting query")
        print(f"📋 Query params: {dict(self.request.query_params)}")
        
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
        print(f"🏪 Initial vendors (approved & online): {initial_count}")
        
        # Search query
        search = self.request.query_params.get('search', '')
        if search:
            print(f"🔎 Applying search filter: '{search}'")
            queryset = queryset.filter(
                Q(business_name__icontains=search) |
                Q(description__icontains=search) |
                Q(business_type__icontains=search) |
                Q(categories__icontains=search)
            )
            search_count = queryset.count()
            print(f"🏪 After search filter: {search_count} vendors")
        
        # Location-based filtering
        user_lat = self.request.query_params.get('latitude')
        user_lon = self.request.query_params.get('longitude')
        
        if user_lat and user_lon:
            try:
                user_lat = float(user_lat)
                user_lon = float(user_lon)
                print(f"📍 User location: ({user_lat}, {user_lon})")
                
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
                        print(f"🏪 '{vendor.business_name}': distance={distance:.2f}km, radius={vendor.delivery_radius}km")
                        
                        if distance <= vendor.delivery_radius:
                            filtered_vendors.append(vendor.id)
                            within_radius += 1
                            print(f"  ✅ INCLUDED: Within delivery range")
                        else:
                            print(f"  ❌ EXCLUDED: Too far ({distance:.2f}km > {vendor.delivery_radius}km)")
                    else:
                        print(f"🏪 '{vendor.business_name}': Missing location/radius data")
                
                print(f"📊 Location filtering: {within_radius}/{total_checked} vendors within delivery radius")
                queryset = queryset.filter(id__in=filtered_vendors)
            except (ValueError, TypeError) as e:
                print(f"❌ Location parsing error: {e}")
        else:
            print("📍 No user location provided - skipping distance filtering")
        
        final_count = queryset.count()
        print(f"🏪 Final result: {final_count} vendors")
        print("🏪 VENDOR SEARCH DEBUG - Complete\n")
        
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