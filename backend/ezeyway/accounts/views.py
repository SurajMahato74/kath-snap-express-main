from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from .models import CustomUser, VendorProfile, CommissionRange, VendorWallet, WalletTransaction, Category, SubCategory, DeliveryRadius, InitialWalletPoints, ChargeRate, FeaturedProductPackage, Slider, PushNotification
from .message_models import Conversation, Message, MessageRead
from .order_models import Order, OrderItem, PaymentTransaction
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

    # Ensure user has auth token
    from rest_framework.authtoken.models import Token
    token, created = Token.objects.get_or_create(user=request.user)

    vendor_profiles = VendorProfile.objects.all().order_by('-user__date_joined')
    context = {
        'vendor_profiles': vendor_profiles,
        'auth_token': token.key
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
        
        if action == 'add_category':
            name = request.POST.get('name')
            description = request.POST.get('description')
            display_order = request.POST.get('display_order')
            icon = request.FILES.get('icon')
            
            if name:
                try:
                    Category.objects.create(
                        name=name,
                        description=description,
                        display_order=int(display_order) if display_order else 0,
                        icon=icon
                    )
                    messages.success(request, 'Category added successfully!')
                except Exception as e:
                    messages.error(request, f'Error adding category: {str(e)}')
            else:
                messages.error(request, 'Category name is required.')
        
        elif action == 'add_subcategory':
            category_id = request.POST.get('category_id')
            name = request.POST.get('subcategory_name')
            description = request.POST.get('subcategory_description')
            display_order = request.POST.get('subcategory_display_order')
            icon = request.FILES.get('subcategory_icon')
            
            if category_id and name:
                try:
                    category = Category.objects.get(id=category_id)
                    SubCategory.objects.create(
                        category=category,
                        name=name,
                        description=description,
                        display_order=int(display_order) if display_order else 0,
                        icon=icon
                    )
                    messages.success(request, 'Subcategory added successfully!')
                except Category.DoesNotExist:
                    messages.error(request, 'Category not found.')
                except Exception as e:
                    messages.error(request, f'Error adding subcategory: {str(e)}')
            else:
                messages.error(request, 'Category and subcategory name are required.')
        
        elif action == 'delete_category':
            category_id = request.POST.get('category_id')
            try:
                category = Category.objects.get(id=category_id)
                if category.icon:
                    category.icon.delete()
                category.delete()
                messages.success(request, 'Category deleted successfully!')
            except Category.DoesNotExist:
                messages.error(request, 'Category not found.')
        
        elif action == 'delete_subcategory':
            subcategory_id = request.POST.get('subcategory_id')
            try:
                subcategory = SubCategory.objects.get(id=subcategory_id)
                if subcategory.icon:
                    subcategory.icon.delete()
                subcategory.delete()
                messages.success(request, 'Subcategory deleted successfully!')
            except SubCategory.DoesNotExist:
                messages.error(request, 'Subcategory not found.')
        
        elif action == 'toggle_category':
            category_id = request.POST.get('category_id')
            try:
                category = Category.objects.get(id=category_id)
                category.is_active = not category.is_active
                category.save()
                status = 'activated' if category.is_active else 'deactivated'
                messages.success(request, f'Category {status} successfully!')
            except Category.DoesNotExist:
                messages.error(request, 'Category not found.')
        
        elif action == 'toggle_subcategory':
            subcategory_id = request.POST.get('subcategory_id')
            try:
                subcategory = SubCategory.objects.get(id=subcategory_id)
                subcategory.is_active = not subcategory.is_active
                subcategory.save()
                status = 'activated' if subcategory.is_active else 'deactivated'
                messages.success(request, f'Subcategory {status} successfully!')
            except SubCategory.DoesNotExist:
                messages.error(request, 'Subcategory not found.')
        
        elif action == 'edit_category':
            category_id = request.POST.get('category_id')
            name = request.POST.get('name')
            description = request.POST.get('description')
            display_order = request.POST.get('display_order')
            icon = request.FILES.get('icon')
            
            if category_id and name:
                try:
                    category = Category.objects.get(id=category_id)
                    category.name = name
                    category.description = description
                    category.display_order = int(display_order) if display_order else 0
                    if icon:
                        if category.icon:
                            category.icon.delete()
                        category.icon = icon
                    category.save()
                    messages.success(request, 'Category updated successfully!')
                except Category.DoesNotExist:
                    messages.error(request, 'Category not found.')
                except Exception as e:
                    messages.error(request, f'Error updating category: {str(e)}')
            else:
                messages.error(request, 'Category name is required.')
        
        elif action == 'edit_subcategory':
            subcategory_id = request.POST.get('subcategory_id')
            name = request.POST.get('subcategory_name')
            description = request.POST.get('subcategory_description')
            display_order = request.POST.get('subcategory_display_order')
            icon = request.FILES.get('subcategory_icon')
            
            if subcategory_id and name:
                try:
                    subcategory = SubCategory.objects.get(id=subcategory_id)
                    subcategory.name = name
                    subcategory.description = description
                    subcategory.display_order = int(display_order) if display_order else 0
                    if icon:
                        if subcategory.icon:
                            subcategory.icon.delete()
                        subcategory.icon = icon
                    subcategory.save()
                    messages.success(request, 'Subcategory updated successfully!')
                except SubCategory.DoesNotExist:
                    messages.error(request, 'Subcategory not found.')
                except Exception as e:
                    messages.error(request, f'Error updating subcategory: {str(e)}')
            else:
                messages.error(request, 'Subcategory name is required.')
        
        return redirect('manage_categories')
    
    categories = Category.objects.prefetch_related('subcategories').all().order_by('display_order', 'name')
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

@login_required
def manage_featured_packages(request):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('login')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            name = request.POST.get('name')
            duration_days = request.POST.get('duration_days')
            amount = request.POST.get('amount')
            package_type = request.POST.get('package_type')
            description = request.POST.get('description')
            
            if name and duration_days and amount:
                try:
                    FeaturedProductPackage.objects.create(
                        name=name,
                        duration_days=int(duration_days),
                        amount=float(amount),
                        package_type=package_type,
                        description=description
                    )
                    messages.success(request, 'Featured package added successfully!')
                except Exception as e:
                    messages.error(request, f'Error adding package: {str(e)}')
            else:
                messages.error(request, 'Name, duration, and amount are required.')
        
        elif action == 'delete':
            package_id = request.POST.get('package_id')
            try:
                FeaturedProductPackage.objects.get(id=package_id).delete()
                messages.success(request, 'Package deleted successfully!')
            except FeaturedProductPackage.DoesNotExist:
                messages.error(request, 'Package not found.')
        
        elif action == 'toggle':
            package_id = request.POST.get('package_id')
            try:
                package = FeaturedProductPackage.objects.get(id=package_id)
                package.is_active = not package.is_active
                package.save()
                status = 'activated' if package.is_active else 'deactivated'
                messages.success(request, f'Package {status} successfully!')
            except FeaturedProductPackage.DoesNotExist:
                messages.error(request, 'Package not found.')
        
        return redirect('manage_featured_packages')
    
    packages = FeaturedProductPackage.objects.all().order_by('duration_days', 'amount')
    context = {
        'packages': packages,
    }
    return render(request, 'accounts/manage_featured_packages.html', context)

@login_required
def manage_sliders(request):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('login')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            title = request.POST.get('title')
            description = request.POST.get('description')
            link_url = request.POST.get('link_url')
            visibility = request.POST.get('visibility')
            display_order = request.POST.get('display_order')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            image = request.FILES.get('image')
            
            if title and image:
                try:
                    # Validate image format
                    allowed_formats = ['gif', 'png', 'svg', 'jpg', 'jpeg']
                    file_extension = image.name.split('.')[-1].lower()
                    
                    if file_extension not in allowed_formats:
                        messages.error(request, 'Invalid file format. Please upload GIF, PNG, SVG, or JPEG files only.')
                        return redirect('manage_sliders')
                    
                    slider = Slider.objects.create(
                        title=title,
                        description=description,
                        image=image,
                        link_url=link_url if link_url else None,
                        visibility=visibility,
                        display_order=int(display_order) if display_order else 0
                    )
                    
                    # Handle date fields
                    if start_date:
                        from datetime import datetime
                        slider.start_date = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
                    if end_date:
                        from datetime import datetime
                        slider.end_date = datetime.strptime(end_date, '%Y-%m-%dT%H:%M')
                    
                    slider.save()
                    messages.success(request, 'Slider added successfully!')
                except Exception as e:
                    messages.error(request, f'Error adding slider: {str(e)}')
            else:
                messages.error(request, 'Title and image are required.')
        
        elif action == 'delete':
            slider_id = request.POST.get('slider_id')
            try:
                slider = Slider.objects.get(id=slider_id)
                # Delete the image file
                if slider.image:
                    slider.image.delete()
                slider.delete()
                messages.success(request, 'Slider deleted successfully!')
            except Slider.DoesNotExist:
                messages.error(request, 'Slider not found.')
        
        elif action == 'toggle':
            slider_id = request.POST.get('slider_id')
            try:
                slider = Slider.objects.get(id=slider_id)
                slider.is_active = not slider.is_active
                slider.save()
                status = 'activated' if slider.is_active else 'deactivated'
                messages.success(request, f'Slider {status} successfully!')
            except Slider.DoesNotExist:
                messages.error(request, 'Slider not found.')
        
        elif action == 'update_order':
            slider_id = request.POST.get('slider_id')
            new_order = request.POST.get('new_order')
            try:
                slider = Slider.objects.get(id=slider_id)
                slider.display_order = int(new_order)
                slider.save()
                messages.success(request, 'Slider order updated successfully!')
            except Slider.DoesNotExist:
                messages.error(request, 'Slider not found.')
            except ValueError:
                messages.error(request, 'Invalid order value.')
        
        return redirect('manage_sliders')
    
    sliders = Slider.objects.all().order_by('display_order', 'created_at')
    context = {
        'sliders': sliders,
    }
    return render(request, 'accounts/manage_sliders.html', context)

@login_required
def manage_push_notifications(request):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('login')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'send':
            title = request.POST.get('title')
            message = request.POST.get('message')
            recipient_type = request.POST.get('recipient_type')
            scheduled_time = request.POST.get('scheduled_time')
            
            if title and message:
                try:
                    notification = PushNotification.objects.create(
                        title=title,
                        message=message,
                        recipient_type=recipient_type,
                        created_by=request.user
                    )
                    
                    if scheduled_time:
                        from datetime import datetime
                        notification.scheduled_time = datetime.strptime(scheduled_time, '%Y-%m-%dT%H:%M')
                        notification.status = 'scheduled'
                    else:
                        notification.status = 'sent'
                        notification.sent_at = timezone.now()
                        # Here you would integrate with your push notification service
                        # For now, we'll simulate sending
                        if recipient_type == 'customer':
                            notification.sent_count = CustomUser.objects.filter(user_type='customer').count()
                        elif recipient_type == 'vendor':
                            notification.sent_count = CustomUser.objects.filter(user_type='vendor').count()
                        else:
                            notification.sent_count = CustomUser.objects.exclude(user_type='superuser').count()
                    
                    notification.save()
                    
                    if notification.status == 'sent':
                        messages.success(request, f'Notification sent to {notification.sent_count} users!')
                    else:
                        messages.success(request, 'Notification scheduled successfully!')
                        
                except Exception as e:
                    messages.error(request, f'Error sending notification: {str(e)}')
            else:
                messages.error(request, 'Title and message are required.')
        
        elif action == 'delete':
            notification_id = request.POST.get('notification_id')
            try:
                PushNotification.objects.get(id=notification_id).delete()
                messages.success(request, 'Notification deleted successfully!')
            except PushNotification.DoesNotExist:
                messages.error(request, 'Notification not found.')
        
        return redirect('manage_push_notifications')
    
    notifications = PushNotification.objects.all().order_by('-created_at')
    context = {
        'notifications': notifications,
    }
    return render(request, 'accounts/manage_push_notifications.html', context)

@login_required
def admin_messages(request):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('login')
    
    user_type = request.GET.get('type', 'all')
    
    # Get all conversations and ensure superadmin is added to them
    all_conversations = Conversation.objects.all().order_by('-updated_at')
    
    # Add superadmin to conversations if not already added
    for conv in all_conversations:
        if not conv.participants.filter(id=request.user.id).exists():
            conv.participants.add(request.user)
    
    # Get unique users who have conversations with superadmin
    user_conversations = {}
    conversations = Conversation.objects.filter(participants=request.user).order_by('-updated_at')
    
    for conv in conversations:
        other_users = conv.participants.exclude(id=request.user.id)
        for user in other_users:
            # Filter by user type if specified
            if user_type == 'customer' and user.user_type != 'customer':
                continue
            elif user_type == 'vendor' and user.user_type != 'vendor':
                continue
            
            # Keep only the latest conversation for each user
            if user.id not in user_conversations or conv.updated_at > user_conversations[user.id]['conversation'].updated_at:
                user_conversations[user.id] = {
                    'user': user,
                    'conversation': conv
                }
    
    # Sort by latest message time
    sorted_conversations = sorted(user_conversations.values(), key=lambda x: x['conversation'].updated_at, reverse=True)
    
    context = {
        'user_conversations': sorted_conversations,
        'user_type': user_type,
    }
    return render(request, 'accounts/admin_messages.html', context)

@login_required
def admin_conversation(request, conversation_id):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('login')
    
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    # Add superadmin to conversation if not already added
    if not conversation.participants.filter(id=request.user.id).exists():
        conversation.participants.add(request.user)
    
    # Handle AJAX request for new messages
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        last_message_count = int(request.GET.get('last_count', 0))
        current_messages = conversation.messages.all().order_by('created_at')
        
        if current_messages.count() > last_message_count:
            new_messages = current_messages[last_message_count:]
            messages_data = []
            
            for msg in new_messages:
                status_icon = ''
                if msg.sender == request.user:
                    if msg.status == 'sent':
                        status_icon = '<i class="fas fa-check"></i>'
                    elif msg.status == 'delivered':
                        status_icon = '<i class="fas fa-check-double"></i>'
                    elif msg.status == 'read':
                        status_icon = '<i class="fas fa-check-double text-primary"></i>'
                
                messages_data.append({
                    'content': msg.content,
                    'created_at': msg.created_at.strftime('%b %d, %H:%M'),
                    'is_sent': msg.sender == request.user,
                    'status_icon': status_icon,
                    'status_display': msg.get_status_display() if msg.sender == request.user else ''
                })
            
            return JsonResponse({'new_messages': messages_data})
        
        return JsonResponse({'new_messages': []})
    
    messages_list = conversation.messages.all().order_by('created_at')[:50]
    
    # Mark messages as read
    for message in messages_list:
        if not message.read_by.filter(user=request.user).exists():
            MessageRead.objects.get_or_create(message=message, user=request.user)
    
    # Get other participant (not superadmin)
    other_participant = conversation.participants.exclude(id=request.user.id).first()
    
    # Send message if POST
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            message = Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content,
                status='sent'
            )
            conversation.updated_at = timezone.now()
            conversation.save()
            
            # Trigger notification for other participants
            from django.core.cache import cache
            cache.set(f'new_message_{conversation.id}', {
                'sender': request.user.username,
                'content': content,
                'timestamp': timezone.now().isoformat(),
                'play_sound': True
            }, 60)  # Cache for 1 minute
            
            return redirect('admin_conversation', conversation_id=conversation_id)
    
    context = {
        'conversation': conversation,
        'messages': messages_list,
        'other_participant': other_participant,
    }
    return render(request, 'accounts/admin_conversation.html', context)

@login_required
def user_profile_details(request, user_id):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('login')
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    # Get user's orders (as customer)
    customer_orders = Order.objects.filter(customer=user).order_by('-created_at')[:10]
    
    # Get vendor orders if user is vendor
    vendor_orders = []
    if user.user_type == 'vendor' and hasattr(user, 'vendor_profile'):
        vendor_orders = Order.objects.filter(vendor=user.vendor_profile).order_by('-created_at')[:10]
    
    # Get payment transactions
    all_orders = list(customer_orders) + list(vendor_orders)
    transactions = PaymentTransaction.objects.filter(
        order__in=all_orders
    ).order_by('-created_at')[:10]
    
    # Get wallet info if vendor
    wallet = None
    if user.user_type == 'vendor' and hasattr(user, 'vendor_profile'):
        wallet = getattr(user.vendor_profile, 'wallet', None)
    
    context = {
        'profile_user': user,
        'customer_orders': customer_orders,
        'vendor_orders': vendor_orders,
        'transactions': transactions,
        'wallet': wallet,
    }
    return render(request, 'accounts/user_profile_details.html', context)

def api_docs(request):
    return render(request, 'accounts/api_docs.html')