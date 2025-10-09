from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    
    # Email Verification
    path('verify-email-prompt/<int:user_id>/', views.verify_email_prompt, name='verify_email_prompt'),
    path('verify-email/<str:token>/', views.verify_email, name='verify_email'),
    path('resend-verification/<int:user_id>/', views.resend_verification, name='resend_verification'),
    
    # Password Reset
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
    
    # OTP System
    path('send-otp/', views.send_otp, name='send_otp'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    
    # Superadmin
    path('superadmin/', views.superadmin_dashboard, name='superadmin_dashboard'),
    path('superadmin/users/', views.manage_users, name='manage_users'),
    path('superadmin/vendors/', views.manage_vendors, name='manage_vendors'),
    path('superadmin/commission-ranges/', views.manage_commission_ranges, name='manage_commission_ranges'),
    path('superadmin/categories/', views.manage_categories, name='manage_categories'),
    path('superadmin/delivery-radius/', views.manage_delivery_radius, name='manage_delivery_radius'),
    path('superadmin/initial-wallet-points/', views.manage_initial_wallet_points, name='manage_initial_wallet_points'),
    
    # Vendor Wallet
    path('vendor/wallet/', views.vendor_wallet_view, name='vendor_wallet'),
    
    # API Documentation
    path('api-docs/', views.api_docs, name='api_docs'),
]