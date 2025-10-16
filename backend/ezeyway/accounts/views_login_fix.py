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
            
            # Proper redirect logic
            if user.is_superuser:
                messages.success(request, f'Welcome back, {user.username}!')
                return redirect('superadmin_dashboard')
            elif user.is_vendor:
                return redirect('vendor_wallet')
            else:
                return redirect('superadmin_dashboard')
        else:
            messages.error(request, 'Invalid username/email or password')
    
    return render(request, 'accounts/login.html')