from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token
import random
import string

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = [
        ('superuser', 'Super Admin'),
        ('vendor', 'Vendor'),
        ('customer', 'Customer'),
    ]
    
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='customer')
    is_customer = models.BooleanField(default=True)  # Can act as customer
    is_vendor = models.BooleanField(default=False)   # Can act as vendor (after approval)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_picture = models.CharField(max_length=500, blank=True, null=True)  # Temporarily using CharField instead of ImageField

    plain_password = models.CharField(max_length=255, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    
    email_otp = models.CharField(max_length=6, blank=True, null=True)
    phone_otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)
    email_verification_sent_at = models.DateTimeField(blank=True, null=True)
    
    password_reset_token = models.CharField(max_length=100, blank=True, null=True)
    password_reset_sent_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith('pbkdf2_'):
            self.plain_password = self.password
        super().save(*args, **kwargs)
    
    def generate_otp(self):
        otp = ''.join(random.choices(string.digits, k=6))
        self.email_otp = otp
        self.phone_otp = otp
        self.otp_created_at = timezone.now()
        self.save()
        return otp
    
    def generate_verification_token(self):
        token = ''.join(random.choices(string.ascii_letters + string.digits, k=50))
        self.email_verification_token = token
        self.email_verification_sent_at = timezone.now()
        self.save()
        return token
    
    def generate_password_reset_token(self):
        token = ''.join(random.choices(string.ascii_letters + string.digits, k=50))
        self.password_reset_token = token
        self.password_reset_sent_at = timezone.now()
        self.save()
        return token
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"
    
    @property
    def is_superadmin(self):
        return self.user_type == 'superuser'
    
    @property
    def is_vendor(self):
        return self.user_type == 'vendor'
    
    @property
    def is_customer(self):
        return self.user_type == 'customer'

class VendorProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='vendor_profile')
    business_name = models.CharField(max_length=200)
    owner_name = models.CharField(max_length=200, default='')
    business_email = models.EmailField()
    business_phone = models.CharField(max_length=15)
    business_address = models.TextField()
    location_address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, default='')
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=20, default='')
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    business_type = models.CharField(
        max_length=50,
        choices=[
            ('retailer', 'Retailer'),
            ('wholesaler', 'Wholesaler'),
            ('manufacturer', 'Manufacturer'),
            ('service_provider', 'Service Provider'),
            ('grocery', 'Grocery Store'),
            ('restaurant', 'Restaurant'),
            ('pharmacy', 'Pharmacy'),
            ('electronics', 'Electronics'),
            ('clothing', 'Clothing'),
            ('bakery', 'Bakery'),
        ],
        default='retailer'
    )
    categories = models.JSONField(default=list)
    description = models.TextField(blank=True, null=True)
    business_license = models.CharField(max_length=100, blank=True, null=True)
    business_license_file = models.CharField(max_length=500, blank=True, null=True)
    gst_number = models.CharField(max_length=50, blank=True, null=True)
    gst_certificate = models.CharField(max_length=500, blank=True, null=True)
    pan_number = models.CharField(max_length=50, blank=True, null=True)
    fssai_license = models.CharField(max_length=500, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    account_holder_name = models.CharField(max_length=200, blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    ifsc_code = models.CharField(max_length=20, blank=True, null=True)
    bank_document = models.CharField(max_length=500, blank=True, null=True)
    delivery_radius = models.FloatField(blank=True, null=True)
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    established_year = models.CharField(max_length=4, blank=True, null=True)
    employee_count = models.CharField(max_length=20, blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    facebook = models.URLField(blank=True, null=True)
    instagram = models.URLField(blank=True, null=True)
    twitter = models.URLField(blank=True, null=True)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    free_delivery_above = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    estimated_delivery_time = models.CharField(max_length=50, blank=True, null=True)
    delivery_slots = models.JSONField(default=list)
    online_ordering = models.BooleanField(default=True)
    home_delivery = models.BooleanField(default=True)
    pickup_service = models.BooleanField(default=True)
    bulk_orders = models.BooleanField(default=False)
    subscription_service = models.BooleanField(default=False)
    loyalty_program = models.BooleanField(default=False)
    business_license_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected')
    ], default='pending')
    gst_certificate_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected')
    ], default='pending')
    fssai_license_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected')
    ], default='pending')
    bank_account_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected')
    ], default='pending')
    is_approved = models.BooleanField(default=False)
    approval_date = models.DateTimeField(blank=True, null=True)
    
    # Operating hours fields
    monday_open = models.TimeField(blank=True, null=True)
    monday_close = models.TimeField(blank=True, null=True)
    monday_closed = models.BooleanField(default=False)
    tuesday_open = models.TimeField(blank=True, null=True)
    tuesday_close = models.TimeField(blank=True, null=True)
    tuesday_closed = models.BooleanField(default=False)
    wednesday_open = models.TimeField(blank=True, null=True)
    wednesday_close = models.TimeField(blank=True, null=True)
    wednesday_closed = models.BooleanField(default=False)
    thursday_open = models.TimeField(blank=True, null=True)
    thursday_close = models.TimeField(blank=True, null=True)
    thursday_closed = models.BooleanField(default=False)
    friday_open = models.TimeField(blank=True, null=True)
    friday_close = models.TimeField(blank=True, null=True)
    friday_closed = models.BooleanField(default=False)
    saturday_open = models.TimeField(blank=True, null=True)
    saturday_close = models.TimeField(blank=True, null=True)
    saturday_closed = models.BooleanField(default=False)
    sunday_open = models.TimeField(blank=True, null=True)
    sunday_close = models.TimeField(blank=True, null=True)
    sunday_closed = models.BooleanField(default=False)
    
    # Status fields
    is_active = models.BooleanField(default=False)  # Current active/inactive status
    status_override = models.BooleanField(default=False)  # Indicates if status is manually overridden
    status_override_date = models.DateField(blank=True, null=True)  # Date of the override
    
    def __str__(self):
        return f"{self.business_name} - {self.user.username}"

class VendorDocument(models.Model):
    vendor_profile = models.ForeignKey(VendorProfile, on_delete=models.CASCADE, related_name='additional_docs')
    document = models.CharField(max_length=500)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Document for {self.vendor_profile.business_name}"

class VendorChangeRequest(models.Model):
    CHANGE_TYPE_CHOICES = [
        ('address', 'Address'),
        ('banking', 'Banking'),
    ]
    
    vendor_profile = models.ForeignKey(VendorProfile, on_delete=models.CASCADE, related_name='change_requests')
    change_type = models.CharField(max_length=20, choices=CHANGE_TYPE_CHOICES)
    new_address = models.TextField(blank=True, null=True)
    new_city = models.CharField(max_length=100, blank=True, null=True)
    new_state = models.CharField(max_length=100, blank=True, null=True)
    new_pincode = models.CharField(max_length=20, blank=True, null=True)
    new_bank_name = models.CharField(max_length=100, blank=True, null=True)
    new_account_holder_name = models.CharField(max_length=200, blank=True, null=True)
    new_account_number = models.CharField(max_length=50, blank=True, null=True)
    new_ifsc_code = models.CharField(max_length=20, blank=True, null=True)
    reason = models.TextField()
    is_approved = models.BooleanField(default=False)
    request_date = models.DateTimeField(auto_now_add=True)
    approval_date = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.change_type} request for {self.vendor_profile.business_name}"

class Product(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('draft', 'Draft'),
        ('archived', 'Archived'),
    ]
    
    vendor = models.ForeignKey(VendorProfile, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100)
    subcategory = models.CharField(max_length=100, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    sku = models.CharField(max_length=100, blank=True, null=True)
    barcode = models.CharField(max_length=100, blank=True, null=True)
    quantity = models.IntegerField(default=0)
    low_stock_threshold = models.IntegerField(blank=True, null=True)
    description = models.TextField()
    short_description = models.TextField(blank=True, null=True)
    tags = models.JSONField(default=list)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    featured = models.BooleanField(default=False)
    seo_title = models.CharField(max_length=200, blank=True, null=True)
    seo_description = models.TextField(blank=True, null=True)
    dynamic_fields = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.vendor.business_name}"

def product_image_upload_path(instance, filename):
    return f'products/{instance.product.vendor.id}/{filename}'

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=product_image_upload_path)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for {self.product.name}"

# Wallet and Commission Models
class VendorWallet(models.Model):
    vendor = models.OneToOneField(VendorProfile, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_earned = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Wallet - {self.vendor.business_name}: ₹{self.balance}"
    
    def add_money(self, amount, description="Wallet Recharge"):
        """Add money to wallet"""
        self.balance += amount
        self.total_earned += amount
        self.save()
        
        # Create transaction record
        WalletTransaction.objects.create(
            wallet=self,
            transaction_type='credit',
            amount=amount,
            description=description,
            status='completed'
        )
    
    def deduct_commission(self, amount, order_amount, description="Commission Deduction"):
        """Deduct commission from wallet"""
        if self.balance >= amount:
            self.balance -= amount
            self.total_spent += amount
            self.save()
            
            # Create transaction record
            WalletTransaction.objects.create(
                wallet=self,
                transaction_type='debit',
                amount=amount,
                description=description,
                order_amount=order_amount,
                status='completed'
            )
            return True
        return False

class CommissionRange(models.Model):
    """Model to store commission ranges set by superadmin"""
    min_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Minimum order amount")
    max_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Maximum order amount (null for unlimited)")
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Fixed commission amount to deduct")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['min_amount']
    
    def __str__(self):
        max_display = f"₹{self.max_amount}" if self.max_amount else "∞"
        return f"₹{self.min_amount} - {max_display}: ₹{self.commission_amount} commission"
    
    @classmethod
    def get_commission_for_amount(cls, order_amount):
        """Get commission amount for a given order amount"""
        ranges = cls.objects.filter(is_active=True).order_by('min_amount')
        
        for commission_range in ranges:
            if order_amount >= commission_range.min_amount:
                if commission_range.max_amount is None or order_amount <= commission_range.max_amount:
                    return commission_range.commission_amount
        
        return 0  # No commission if no range matches

class WalletTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('credit', 'Credit'),
        ('debit', 'Debit'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    wallet = models.ForeignKey(VendorWallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    order_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Original order amount for commission transactions")
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    reference_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.wallet.vendor.business_name} - {self.transaction_type.upper()} ₹{self.amount}"

class UserFavorite(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='favorites')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'product')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.product.name}"

class Cart(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Cart - {self.user.username}"
    
    @property
    def total_items(self):
        return sum(item.quantity for item in self.items.all())
    
    @property
    def subtotal(self):
        return sum(item.total_price for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('cart', 'product')
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    @property
    def total_price(self):
        return self.product.price * self.quantity

@receiver(post_save, sender=CustomUser)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)

@receiver(post_save, sender=VendorProfile)
def create_vendor_wallet(sender, instance=None, created=False, **kwargs):
    if created:
        # Get initial wallet points set by admin
        initial_points = InitialWalletPoints.objects.first()
        initial_balance = initial_points.points if initial_points else 0
        
        # Create wallet with initial balance
        wallet = VendorWallet.objects.create(
            vendor=instance,
            balance=initial_balance,
            total_earned=initial_balance
        )
        
        # Create transaction record for initial points
        if initial_balance > 0:
            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='credit',
                amount=initial_balance,
                description='Initial wallet points from admin',
                status='completed'
            )

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class DeliveryRadius(models.Model):
    radius = models.FloatField(help_text="Delivery radius in kilometers")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Delivery Radii"
        ordering = ['radius']
    
    def __str__(self):
        return f"{self.radius} km"

class InitialWalletPoints(models.Model):
    points = models.DecimalField(max_digits=10, decimal_places=2, help_text="Initial wallet points for new vendors")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Initial Wallet Points"
        ordering = ['points']
    
    def __str__(self):
        return f"₹{self.points}"

class ChargeRate(models.Model):
    min_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Minimum order amount")
    max_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Maximum order amount (null for unlimited)")
    charge = models.DecimalField(max_digits=10, decimal_places=2, help_text="Charge amount for this range")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['min_amount']
    
    def __str__(self):
        max_display = f"₹{self.max_amount}" if self.max_amount else "∞"
        return f"₹{self.min_amount} - {max_display}: ₹{self.charge} charge"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        # Check for overlapping ranges
        existing_ranges = ChargeRate.objects.exclude(id=self.id)
        for existing in existing_ranges:
            # Check if ranges overlap
            existing_max = existing.max_amount or float('inf')
            current_max = self.max_amount or float('inf')
            
            if (self.min_amount < existing_max and 
                (self.max_amount is None or self.max_amount > existing.min_amount)):
                raise ValidationError(f'Range overlaps with existing range: {existing}')
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

# Import order models
from .order_models import *

# Import message models
from .message_models import *