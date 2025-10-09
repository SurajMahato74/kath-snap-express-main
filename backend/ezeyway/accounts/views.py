from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from .models import CustomUser, VendorProfile, CommissionRange, VendorWallet, WalletTransaction, Category, DeliveryRadius, InitialWalletPoints, ChargeRate
from .utils import send_otp_email, send_verification_email, send_password_reset_email

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Superusers don't need email verification
            if not user.email_verified and not user.is_superuser:
                messages.warning(request, 'Please verify your email before logging in.')
                return redirect('verify_email_prompt', user_id=user.id)
            
            login(request, user)
            if user.is_superuser:
                return redirect('superadmin_dashboard')
            elif user.is_vendor:
                return redirect('vendor_wallet')
            else:
                return redirect('superadmin_dashboard')
        else:
            messages.error(request, 'Invalid username/email or password')
    
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def superadmin_dashboard(request):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superadmin privileges required.')
        return redirect('login')
    
    # Dashboard statistics
    total_users = CustomUser.objects.count()
    total_customers = CustomUser.objects.filter(user_type='customer').count()
    total_vendors = CustomUser.objects.filter(user_type='vendor').count()
    pending_vendors = VendorProfile.objects.filter(is_approved=False).count()
    
    context = {
        'total_users': total_users,
        'total_customers': total_customers,
        'total_vendors': total_vendors,
        'pending_vendors': pending_vendors,
        'recent_users': CustomUser.objects.order_by('-date_joined')[:10],
        'pending_vendor_profiles': VendorProfile.objects.filter(is_approved=False)[:5],
    }
    
    return render(request, 'accounts/superadmin_dashboard.html', context)

@login_required
def manage_users(request):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('login')
    
    users = CustomUser.objects.all().order_by('-date_joined')
    return render(request, 'accounts/manage_users.html', {'users': users})

@login_required
def manage_vendors(request):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('login')

    vendor_profiles = VendorProfile.objects.all().order_by('-user__date_joined')
    context = {
        'vendor_profiles': vendor_profiles,
        'auth_token': request.user.auth_token.key if hasattr(request.user, 'auth_token') else None
    }
    return render(request, 'accounts/manage_vendors.html', context)

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        user_type = request.POST.get('user_type', 'customer')
        phone_number = request.POST.get('phone_number')
        
        # Check if user exists
        if CustomUser.objects.filter(Q(username=username) | Q(email=email)).exists():
            messages.error(request, 'Username or email already exists')
            return render(request, 'accounts/register.html')
        
        # Create user
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            user_type=user_type,
            phone_number=phone_number,
            plain_password=password
        )
        
        # Generate and send verification email
        token = user.generate_verification_token()
        send_verification_email(user, token)
        
        messages.success(request, 'Registration successful! Please check your email to verify your account.')
        return redirect('verify_email_prompt', user_id=user.id)
    
    return render(request, 'accounts/register.html')

def verify_email_prompt(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    return render(request, 'accounts/verify_email_prompt.html', {'user': user})

def verify_email(request, token):
    try:
        user = CustomUser.objects.get(email_verification_token=token)
        
        # Check if token is expired
        if user.email_verification_sent_at:
            expiry_time = user.email_verification_sent_at + timedelta(hours=settings.VERIFICATION_TOKEN_EXPIRY_HOURS)
            if timezone.now() > expiry_time:
                messages.error(request, 'Verification link has expired. Please request a new one.')
                return redirect('resend_verification', user_id=user.id)
        
        user.email_verified = True
        user.is_verified = True
        user.email_verification_token = None
        user.save()
        
        messages.success(request, 'Email verified successfully! You can now log in.')
        return redirect('login')
        
    except CustomUser.DoesNotExist:
        messages.error(request, 'Invalid verification link.')
        return redirect('login')

def resend_verification(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    
    if user.email_verified:
        messages.info(request, 'Email is already verified.')
        return redirect('login')
    
    token = user.generate_verification_token()
    send_verification_email(user, token)
    
    messages.success(request, 'Verification email sent! Please check your inbox.')
    return render(request, 'accounts/verify_email_prompt.html', {'user': user})

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            user = CustomUser.objects.get(email=email)
            token = user.generate_password_reset_token()
            send_password_reset_email(user, token)
            
            messages.success(request, 'Password reset link sent to your email.')
            return redirect('login')
            
        except CustomUser.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
    
    return render(request, 'accounts/forgot_password.html')

def reset_password(request, token):
    try:
        user = CustomUser.objects.get(password_reset_token=token)
        
        # Check if token is expired
        if user.password_reset_sent_at:
            expiry_time = user.password_reset_sent_at + timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRY_HOURS)
            if timezone.now() > expiry_time:
                messages.error(request, 'Password reset link has expired. Please request a new one.')
                return redirect('forgot_password')
        
        if request.method == 'POST':
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            
            if password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'accounts/reset_password.html', {'token': token})
            
            user.set_password(password)
            user.plain_password = password
            user.password_reset_token = None
            user.save()
            
            messages.success(request, 'Password reset successfully! You can now log in.')
            return redirect('login')
        
        return render(request, 'accounts/reset_password.html', {'token': token})
        
    except CustomUser.DoesNotExist:
        messages.error(request, 'Invalid password reset link.')
        return redirect('forgot_password')

def send_otp(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            user = CustomUser.objects.get(email=email)
            otp = user.generate_otp()
            send_otp_email(user, otp)
            
            return JsonResponse({'success': True, 'message': 'OTP sent successfully'})
            
        except CustomUser.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'User not found'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

def verify_otp(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        otp = request.POST.get('otp')
        
        try:
            user = CustomUser.objects.get(email=email)
            
            # Check if OTP is expired
            if user.otp_created_at:
                expiry_time = user.otp_created_at + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
                if timezone.now() > expiry_time:
                    return JsonResponse({'success': False, 'message': 'OTP has expired'})
            
            if user.email_otp == otp:
                user.email_verified = True
                user.is_verified = True
                user.email_otp = None
                user.phone_otp = None
                user.save()
                
                return JsonResponse({'success': True, 'message': 'OTP verified successfully'})
            else:
                return JsonResponse({'success': False, 'message': 'Invalid OTP'})
                
        except CustomUser.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'User not found'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

@login_required
def manage_commission_ranges(request):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('login')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            min_amount = request.POST.get('min_amount')
            max_amount = request.POST.get('max_amount')
            commission_amount = request.POST.get('commission_amount')
            
            try:
                CommissionRange.objects.create(
                    min_amount=min_amount,
                    max_amount=max_amount if max_amount else None,
                    commission_amount=commission_amount
                )
                messages.success(request, 'Commission range added successfully!')
            except Exception as e:
                messages.error(request, f'Error adding commission range: {str(e)}')
        
        elif action == 'delete':
            range_id = request.POST.get('range_id')
            try:
                CommissionRange.objects.get(id=range_id).delete()
                messages.success(request, 'Commission range deleted successfully!')
            except CommissionRange.DoesNotExist:
                messages.error(request, 'Commission range not found.')
        
        elif action == 'toggle':
            range_id = request.POST.get('range_id')
            try:
                commission_range = CommissionRange.objects.get(id=range_id)
                commission_range.is_active = not commission_range.is_active
                commission_range.save()
                status = 'activated' if commission_range.is_active else 'deactivated'
                messages.success(request, f'Commission range {status} successfully!')
            except CommissionRange.DoesNotExist:
                messages.error(request, 'Commission range not found.')
        
        return redirect('manage_commission_ranges')
    
    commission_ranges = CommissionRange.objects.all().order_by('min_amount')
    context = {
        'commission_ranges': commission_ranges,
    }
    return render(request, 'accounts/manage_commission_ranges.html', context)

@login_required
def vendor_wallet_view(request):
    if not request.user.is_vendor:
        messages.error(request, 'Access denied.')
        return redirect('login')
    
    try:
        vendor_profile = request.user.vendor_profile
        wallet, created = VendorWallet.objects.get_or_create(vendor=vendor_profile)
        
        # Get recent transactions
        transactions = wallet.transactions.all()[:20]
        
        context = {
            'wallet': wallet,
            'transactions': transactions,
        }
        return render(request, 'accounts/vendor_wallet.html', context)
    except VendorProfile.DoesNotExist:
        messages.error(request, 'Vendor profile not found.')
        return redirect('login')

@login_required
def manage_categories(request):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('login')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            name = request.POST.get('name')
            if name:
                try:
                    Category.objects.create(name=name)
                    messages.success(request, 'Category added successfully!')
                except Exception as e:
                    messages.error(request, f'Error adding category: {str(e)}')
            else:
                messages.error(request, 'Category name is required.')
        
        elif action == 'delete':
            category_id = request.POST.get('category_id')
            try:
                Category.objects.get(id=category_id).delete()
                messages.success(request, 'Category deleted successfully!')
            except Category.DoesNotExist:
                messages.error(request, 'Category not found.')
        
        return redirect('manage_categories')
    
    categories = Category.objects.all().order_by('name')
    context = {
        'categories': categories,
    }
    return render(request, 'accounts/manage_categories.html', context)

@login_required
def manage_delivery_radius(request):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('login')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            radius = request.POST.get('radius')
            if radius:
                try:
                    DeliveryRadius.objects.create(radius=float(radius))
                    messages.success(request, 'Delivery radius added successfully!')
                except Exception as e:
                    messages.error(request, f'Error adding delivery radius: {str(e)}')
            else:
                messages.error(request, 'Radius value is required.')
        
        elif action == 'delete':
            radius_id = request.POST.get('radius_id')
            try:
                DeliveryRadius.objects.get(id=radius_id).delete()
                messages.success(request, 'Delivery radius deleted successfully!')
            except DeliveryRadius.DoesNotExist:
                messages.error(request, 'Delivery radius not found.')
        
        return redirect('manage_delivery_radius')
    
    delivery_radii = DeliveryRadius.objects.all().order_by('radius')
    context = {
        'delivery_radii': delivery_radii,
    }
    return render(request, 'accounts/manage_delivery_radius.html', context)

@login_required
def manage_initial_wallet_points(request):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('login')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_points':
            points = request.POST.get('points')
            if points:
                try:
                    InitialWalletPoints.objects.create(points=float(points))
                    messages.success(request, 'Initial wallet points added successfully!')
                except Exception as e:
                    messages.error(request, f'Error adding initial wallet points: {str(e)}')
            else:
                messages.error(request, 'Points value is required.')
        
        elif action == 'delete_points':
            points_id = request.POST.get('points_id')
            try:
                InitialWalletPoints.objects.get(id=points_id).delete()
                messages.success(request, 'Initial wallet points deleted successfully!')
            except InitialWalletPoints.DoesNotExist:
                messages.error(request, 'Initial wallet points not found.')
        
        elif action == 'add_charge':
            min_amount = request.POST.get('min_amount')
            max_amount = request.POST.get('max_amount')
            charge = request.POST.get('charge')
            
            if min_amount and charge:
                try:
                    ChargeRate.objects.create(
                        min_amount=float(min_amount),
                        max_amount=float(max_amount) if max_amount else None,
                        charge=float(charge)
                    )
                    messages.success(request, 'Charge rate added successfully!')
                except Exception as e:
                    messages.error(request, f'Error adding charge rate: {str(e)}')
            else:
                messages.error(request, 'Min amount and charge are required.')
        
        elif action == 'delete_charge':
            charge_id = request.POST.get('charge_id')
            try:
                ChargeRate.objects.get(id=charge_id).delete()
                messages.success(request, 'Charge rate deleted successfully!')
            except ChargeRate.DoesNotExist:
                messages.error(request, 'Charge rate not found.')
        
        return redirect('manage_initial_wallet_points')
    
    wallet_points = InitialWalletPoints.objects.all().order_by('points')
    charge_rates = ChargeRate.objects.all().order_by('min_amount')
    context = {
        'wallet_points': wallet_points,
        'charge_rates': charge_rates,
    }
    return render(request, 'accounts/manage_initial_wallet_points.html', context)

def api_docs(request):
    return render(request, 'accounts/api_docs.html')