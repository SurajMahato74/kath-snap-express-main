from rest_framework import serializers
from django.contrib.auth import authenticate
from django.db.models import Q
from django.utils import timezone
from datetime import time
from .models import CustomUser, VendorProfile, VendorDocument, Product, ProductImage, VendorWallet, WalletTransaction, UserFavorite, Cart, CartItem

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'user_type', 'phone_number', 'address', 
                  'date_of_birth', 'profile_picture', 'is_verified', 'email_verified', 
                  'phone_verified', 'created_at']
        read_only_fields = ['id', 'created_at', 'is_verified', 'email_verified', 'phone_verified']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'user_type', 'phone_number']
    
    def validate(self, attrs):
        if CustomUser.objects.filter(Q(username=attrs['username']) | Q(email=attrs['email'])).exists():
            raise serializers.ValidationError("Username or email already exists")
        return attrs
    
    def create(self, validated_data):
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(
            password=password,
            plain_password=password,
            **validated_data
        )
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            attrs['user'] = user
            attrs['needs_verification'] = not user.email_verified and not user.is_superadmin
        else:
            raise serializers.ValidationError('Must include username and password')

        return attrs

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=6)
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect')
        return value

class SimpleChangePasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(min_length=6)

    def update_user_password(self, user):
        password = self.validated_data['new_password']
        user.set_password(password)
        user.plain_password = password  # store plain password if your model has it
        user.save()
        return user
    
class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    def validate_email(self, value):
        if not CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError('No account found with this email')
        return value

class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(min_length=6)
    confirm_password = serializers.CharField()
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError('Passwords do not match')
        return attrs

class OTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, min_length=6)

class VendorProfileSerializer(serializers.ModelSerializer):
    categories = serializers.JSONField()
    business_name = serializers.CharField(required=False)
    business_email = serializers.EmailField(required=False)
    business_phone = serializers.CharField(required=False)
    business_address = serializers.CharField(required=False)
    state = serializers.CharField(required=False)
    business_license_file = serializers.FileField(required=False, allow_null=True)
    gst_certificate = serializers.FileField(required=False, allow_null=True)
    fssai_license = serializers.FileField(required=False, allow_null=True)
    bank_document = serializers.FileField(required=False, allow_null=True)
    additional_docs = serializers.SerializerMethodField()
    user_info = serializers.SerializerMethodField()
    business_license_file_url = serializers.SerializerMethodField()
    gst_certificate_url = serializers.SerializerMethodField()
    fssai_license_url = serializers.SerializerMethodField()
    bank_document_url = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = VendorProfile
        fields = [
            'id', 'user', 'user_info', 'business_name', 'owner_name', 'business_email', 'business_phone',
            'business_address', 'location_address', 'city', 'state', 'pincode',
            'latitude', 'longitude', 'business_type', 'categories', 'description',
            'business_license', 'business_license_file', 'business_license_file_url', 'gst_number', 'gst_certificate', 'gst_certificate_url',
            'pan_number', 'fssai_license', 'fssai_license_url', 'bank_name', 'account_holder_name',
            'account_number', 'ifsc_code', 'bank_document', 'bank_document_url', 'delivery_radius',
            'min_order_amount', 'is_approved', 'approval_date', 'additional_docs',
            'established_year', 'employee_count', 'website', 'facebook', 'instagram', 'twitter',
            'delivery_fee', 'free_delivery_above', 'estimated_delivery_time', 'delivery_slots',
            'online_ordering', 'home_delivery', 'pickup_service', 'bulk_orders', 'subscription_service',
            'loyalty_program', 'business_license_status', 'gst_certificate_status', 'fssai_license_status',
            'bank_account_status',
            'monday_open', 'monday_close', 'monday_closed',
            'tuesday_open', 'tuesday_close', 'tuesday_closed',
            'wednesday_open', 'wednesday_close', 'wednesday_closed',
            'thursday_open', 'thursday_close', 'thursday_closed',
            'friday_open', 'friday_close', 'friday_closed',
            'saturday_open', 'saturday_close', 'saturday_closed',
            'sunday_open', 'sunday_close', 'sunday_closed',
            'is_active', 'status_override', 'status_override_date'
        ]
        read_only_fields = ['id', 'user', 'is_approved', 'approval_date', 'is_active']
    
    def update(self, instance, validated_data):
        # Handle file uploads separately
        for field_name, field_value in validated_data.items():
            setattr(instance, field_name, field_value)
        instance.save()
        return instance

    def get_additional_docs(self, obj):
        request = self.context.get('request')
        docs = obj.additional_docs.all()
        return [{
            'id': doc.id,
            'document': request.build_absolute_uri(f'/media/{doc.document}') if doc.document and request else f'/media/{doc.document}' if doc.document else None,
            'uploaded_at': doc.uploaded_at
        } for doc in docs]

    def get_user_info(self, obj):
        request = self.context.get('request')
        profile_picture_url = None
        if obj.user.profile_picture:
            if not request:
                profile_picture_url = f'/media/{obj.user.profile_picture}'
            elif 'ngrok-free.app' in request.get_host():
                profile_picture_url = f'https://{request.get_host()}/media/{obj.user.profile_picture}'
            else:
                profile_picture_url = request.build_absolute_uri(f'/media/{obj.user.profile_picture}')
        
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'email': obj.user.email,
            'phone_number': obj.user.phone_number,
            'date_joined': obj.user.date_joined,
            'profile_picture': profile_picture_url,
            'plain_password': obj.user.plain_password
        }

    def get_business_license_file_url(self, obj):
        request = self.context.get('request')
        if not obj.business_license_file:
            return None
        if not request:
            return f'/media/{obj.business_license_file}'
        if 'ngrok-free.app' in request.get_host():
            return f'https://{request.get_host()}/media/{obj.business_license_file}'
        return request.build_absolute_uri(f'/media/{obj.business_license_file}')

    def get_gst_certificate_url(self, obj):
        request = self.context.get('request')
        if not obj.gst_certificate:
            return None
        if not request:
            return f'/media/{obj.gst_certificate}'
        return request.build_absolute_uri(f'/media/{obj.gst_certificate}')

    def get_fssai_license_url(self, obj):
        request = self.context.get('request')
        if not obj.fssai_license:
            return None
        if not request:
            return f'/media/{obj.fssai_license}'
        return request.build_absolute_uri(f'/media/{obj.fssai_license}')

    def get_bank_document_url(self, obj):
        request = self.context.get('request')
        if not obj.bank_document:
            return None
        if not request:
            return f'/media/{obj.bank_document}'
        return request.build_absolute_uri(f'/media/{obj.bank_document}')

    def get_is_active(self, obj):
        # If status is overridden and the override is for today, return the stored is_active
        if obj.status_override and obj.status_override_date == timezone.now().date():
            return obj.is_active

        # Otherwise, compute is_active based on the current time and schedule
        current_time = timezone.now().time()
        current_day = timezone.now().strftime('%A').lower()

        day_open = getattr(obj, f'{current_day}_open')
        day_close = getattr(obj, f'{current_day}_close')
        day_closed = getattr(obj, f'{current_day}_closed')

        if day_closed or not day_open or not day_close:
            return False

        return day_open <= current_time < day_close

    def validate(self, attrs):
        request = self.context.get('request')
        
        # Only apply required field validation for POST requests (creating new profiles)
        if request and request.method == 'POST':
            required_fields = ['business_name', 'business_email', 'business_phone', 'business_address', 
                               'city', 'state', 'pincode', 'business_type']
            for field in required_fields:
                if field not in attrs or not attrs[field]:
                    raise serializers.ValidationError({field: f"{field.replace('_', ' ').title()} is required."})
        
        # For PATCH/PUT requests, only validate fields that are being updated
        # Skip required field validation for partial updates

        if 'business_email' in attrs:
            from django.core.validators import validate_email
            try:
                validate_email(attrs['business_email'])
            except serializers.ValidationError:
                raise serializers.ValidationError({'business_email': 'Invalid email format.'})

        if 'business_phone' in attrs:
            phone = attrs['business_phone']
            if not (phone.isdigit() and 10 <= len(phone) <= 15):
                raise serializers.ValidationError({'business_phone': 'Phone number must be 10-15 digits.'})

        if 'latitude' in attrs and attrs['latitude'] is not None:
            if not (-90 <= attrs['latitude'] <= 90):
                raise serializers.ValidationError({'latitude': 'Latitude must be between -90 and 90.'})
        if 'longitude' in attrs and attrs['longitude'] is not None:
            if not (-180 <= attrs['longitude'] <= 180):
                raise serializers.ValidationError({'longitude': 'Longitude must be between -180 and 180.'})

        valid_business_types = [choice[0] for choice in VendorProfile._meta.get_field('business_type').choices]
        if 'business_type' in attrs and attrs['business_type'] not in valid_business_types:
            raise serializers.ValidationError({'business_type': f'Invalid business type. Must be one of: {", ".join(valid_business_types)}.'})

        if 'categories' in attrs:
            if not isinstance(attrs['categories'], list):
                raise serializers.ValidationError({'categories': 'Categories must be a list.'})

        if 'delivery_radius' in attrs and attrs['delivery_radius'] is not None:
            if attrs['delivery_radius'] < 0:
                raise serializers.ValidationError({'delivery_radius': 'Delivery radius cannot be negative.'})
        if 'min_order_amount' in attrs and attrs['min_order_amount'] is not None:
            if attrs['min_order_amount'] < 0:
                raise serializers.ValidationError({'min_order_amount': 'Minimum order amount cannot be negative.'})

        # Validate operating hours
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for day in days:
            open_field = f'{day}_open'
            close_field = f'{day}_close'
            closed_field = f'{day}_closed'
            
            if open_field in attrs and close_field in attrs:
                if attrs.get(closed_field, False):
                    continue  # Skip time validation if day is closed
                if attrs[open_field] and attrs[close_field]:
                    if attrs[open_field] >= attrs[close_field]:
                        raise serializers.ValidationError({open_field: f'{day.capitalize()} opening time must be before closing time.'})

        return attrs

class VendorDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = VendorDocument
        fields = ['id', 'vendor_profile', 'document', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']

    def validate(self, attrs):
        if 'vendor_profile' not in attrs:
            raise serializers.ValidationError({'vendor_profile': 'Vendor profile is required.'})
        if 'document' not in attrs:
            raise serializers.ValidationError({'document': 'Document is required.'})
        return attrs

class AdminUserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'confirm_password', 'user_type',
                  'phone_number', 'first_name', 'last_name', 'address', 'date_of_birth']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        
        if CustomUser.objects.filter(Q(username=attrs['username']) | Q(email=attrs['email'])).exists():
            raise serializers.ValidationError("Username or email already exists")
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(
            password=password,
            plain_password=password,
            email_verified=True,
            is_verified=True,
            **validated_data
        )
        return user

class AdminUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'user_type', 'phone_number', 'first_name',
                  'last_name', 'address', 'date_of_birth', 'is_active', 'email_verified']
    
    def validate_username(self, value):
        if CustomUser.objects.filter(username=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("Username already exists")
        return value
    
    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("Email already exists")
        return value

class ProductImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'image_url', 'is_primary']
        read_only_fields = ['id']
    
    def get_image_url(self, obj):
        request = self.context.get('request')
        if request and obj.image:
            return request.build_absolute_uri(obj.image.url)
        elif obj.image:
            return obj.image.url
        return None

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    image_files = serializers.ListField(
        child=serializers.FileField(), write_only=True, required=False
    )
    cost_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'category', 'subcategory', 'price', 'cost_price',
            'sku', 'barcode', 'quantity', 'low_stock_threshold',
            'description', 'short_description', 'tags', 'status', 'featured',
            'seo_title', 'seo_description', 'dynamic_fields', 'images', 'image_files',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        image_files = validated_data.pop('image_files', [])
        product = Product.objects.create(**validated_data)
        
        for i, image_file in enumerate(image_files):
            ProductImage.objects.create(
                product=product,
                image=image_file,
                is_primary=(i == 0)
            )
        
        return product
    
    def update(self, instance, validated_data):
        image_files = validated_data.pop('image_files', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if image_files:
            # Add new images without deleting existing ones
            existing_count = instance.images.count()
            for i, image_file in enumerate(image_files):
                ProductImage.objects.create(
                    product=instance,
                    image=image_file,
                    is_primary=(existing_count == 0 and i == 0)
                )
        
        return instance

class UserStatsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    total_customers = serializers.IntegerField()
    total_vendors = serializers.IntegerField()
    total_superusers = serializers.IntegerField()
    pending_vendors = serializers.IntegerField()
    verified_users = serializers.IntegerField()
    unverified_users = serializers.IntegerField()

class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = ['id', 'transaction_type', 'amount', 'description', 'order_amount', 
                 'payment_method', 'reference_id', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class VendorWalletSerializer(serializers.ModelSerializer):
    transactions = WalletTransactionSerializer(many=True, read_only=True)
    business_name = serializers.CharField(source='vendor.business_name', read_only=True)
    
    class Meta:
        model = VendorWallet
        fields = ['id', 'balance', 'total_earned', 'total_spent', 'business_name', 
                 'transactions', 'created_at', 'updated_at']
        read_only_fields = ['id', 'total_earned', 'total_spent', 'created_at', 'updated_at']

class AddMoneySerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=1)
    payment_method = serializers.CharField(max_length=50)
    reference_id = serializers.CharField(max_length=100, required=False)

class CustomerProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    vendor_name = serializers.CharField(source='vendor.business_name', read_only=True)
    vendor_id = serializers.IntegerField(source='vendor.id', read_only=True)
    vendor_latitude = serializers.FloatField(source='vendor.latitude', read_only=True)
    vendor_longitude = serializers.FloatField(source='vendor.longitude', read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'category', 'subcategory', 'price', 'quantity',
            'description', 'short_description', 'tags', 'images',
            'vendor_name', 'vendor_id', 'vendor_latitude', 'vendor_longitude', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class UserFavoriteSerializer(serializers.ModelSerializer):
    product = CustomerProductSerializer(read_only=True)
    
    class Meta:
        model = UserFavorite
        fields = ['id', 'product', 'created_at']
        read_only_fields = ['id', 'created_at']

class CartItemSerializer(serializers.ModelSerializer):
    product = CustomerProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity', 'total_price', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_product_id(self, value):
        try:
            product = Product.objects.get(id=value, status='active')
            return value
        except Product.DoesNotExist:
            raise serializers.ValidationError('Product not found or inactive')
    
    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError('Quantity must be greater than 0')
        return value

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_items', 'subtotal', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

# Import order serializers
from .order_serializers import *

# Import message serializers
from .message_serializers import *