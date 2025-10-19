from django.urls import path, include
from . import api_views, notification_views
from .notification_api import check_notifications
from .broadcast_api import broadcast_message
from .token_refresh_api import refresh_token_api

urlpatterns = [
    # Test API
    path('test/', api_views.test_api, name='api_test'),
    path('health/', api_views.health_check, name='api_health'),
    path('vendor/status/test/', api_views.vendor_status_test, name='api_vendor_status_test'),
    
    # Authentication APIs
    path('register/', api_views.register_api, name='api_register'),
    path('login/', api_views.login_api, name='api_login'),
    path('logout/', api_views.logout_api, name='api_logout'),
    path('auth/google/', api_views.google_oauth_api, name='api_google_oauth'),
    path('auth/facebook/', api_views.facebook_oauth_api, name='api_facebook_oauth'),
    path('setup-password/', api_views.setup_password_api, name='api_setup_password'),
    path('check-password-setup/', api_views.check_password_setup_api, name='api_check_password_setup'),
    path('agree-privacy-policy/', api_views.agree_privacy_policy_api, name='api_agree_privacy_policy'),
    
    # Profile APIs
    path('profile/', api_views.profile_api, name='api_profile'),
    path('profile/update/', api_views.update_profile_api, name='api_update_profile'),
    path('profile/upload-picture/', api_views.upload_profile_picture_api, name='api_upload_profile_picture'),
    path('vendor/status/', api_views.vendor_status_api, name='api_vendor_status'),
    path('vendor/toggle-status/', api_views.toggle_vendor_status_api, name='api_toggle_vendor_status'),
    path('switch-role/', api_views.switch_role_api, name='api_switch_role'),
    path('change-password/', api_views.change_password_api, name='api_change_password'),
    path('change-password/simple/', api_views.SimpleChangePasswordView.as_view(), name='api_simple_change_password'),

    
    # Email Verification APIs
    path('verify-email/<str:token>/', api_views.verify_email_api, name='api_verify_email'),
    path('resend-verification/', api_views.resend_verification_api, name='api_resend_verification'),
    
    # Password Reset APIs
    path('forgot-password/', api_views.forgot_password_api, name='api_forgot_password'),
    path('reset-password/', api_views.reset_password_api, name='api_reset_password'),
    
    # OTP APIs
    path('send-otp/', api_views.send_otp_api, name='api_send_otp'),
    path('verify-otp/', api_views.verify_otp_api, name='api_verify_otp'),
    path('update-email/', api_views.update_email_api, name='api_update_email'),
    
    # Categories API
    path('categories/', api_views.get_categories_api, name='api_get_categories'),
    path('categories/<str:category_name>/subcategories/', api_views.get_subcategories_api, name='api_get_subcategories'),
    
    # Delivery Radius API
    path('delivery-radius/', api_views.get_delivery_radius_api, name='api_get_delivery_radius'),
    
    # Vendor APIs
    path('vendor-profiles/', api_views.VendorProfileListCreateView.as_view(), name='api_vendor_profiles'),
    path('vendor-profiles/<int:pk>/', api_views.VendorProfileDetailView.as_view(), name='api_vendor_profile_detail'),
    path('vendor-profiles/<int:pk>/toggle-status/', api_views.vendor_toggle_status_api, name='api_vendor_toggle_status'),
    path('vendor-documents/', api_views.VendorDocumentListCreateView.as_view(), name='api_vendor_documents'),
    path('vendor-shop-images/', api_views.VendorShopImageListCreateView.as_view(), name='api_vendor_shop_images'),
    path('complete-onboarding/', api_views.complete_vendor_onboarding, name='api_complete_onboarding'),
    
    # Product APIs
    path('products/', api_views.ProductListCreateView.as_view(), name='api_products'),
    path('products/<int:pk>/', api_views.ProductDetailView.as_view(), name='api_product_detail'),
    path('products/<int:product_id>/images/<int:image_id>/', api_views.delete_product_image, name='api_delete_product_image'),
    path('products/<int:product_id>/images/<int:image_id>/set-primary/', api_views.set_primary_image, name='api_set_primary_image'),
    
    # Wallet APIs
    path('vendor-wallet/', api_views.vendor_wallet_api, name='api_vendor_wallet'),
    path('wallet/transactions/', api_views.wallet_transactions_api, name='api_wallet_transactions'),
    path('wallet/add-money/', api_views.add_money_api, name='api_add_money'),
    path('wallet/khalti-payment/', api_views.initiate_khalti_payment, name='api_khalti_payment'),
    path('wallet/khalti-verify/', api_views.verify_khalti_payment, name='api_khalti_verify'),
    path('wallet/check-balance/', api_views.check_wallet_balance_api, name='api_check_wallet_balance'),
    
    # Customer Search APIs
    path('search/products/', api_views.CustomerProductSearchView.as_view(), name='api_customer_product_search'),
    path('search/vendors/', api_views.CustomerVendorSearchView.as_view(), name='api_customer_vendor_search'),
    
    # Customer Vendor Profile API
    path('vendors/<int:vendor_id>/', api_views.CustomerVendorProfileView.as_view(), name='api_customer_vendor_profile'),
    
    # Favorite APIs
    path('favorites/', api_views.UserFavoriteListView.as_view(), name='api_user_favorites'),
    path('favorites/toggle/', api_views.toggle_favorite_api, name='api_toggle_favorite'),
    
    # Cart APIs
    path('cart/', api_views.get_cart_api, name='api_get_cart'),
    path('cart/add/', api_views.add_to_cart_api, name='api_add_to_cart'),
    path('cart/items/<int:item_id>/update/', api_views.update_cart_item_api, name='api_update_cart_item'),
    path('cart/items/<int:item_id>/remove/', api_views.remove_from_cart_api, name='api_remove_from_cart'),
    path('cart/clear/', api_views.clear_cart_api, name='api_clear_cart'),
    
    # Admin APIs
    path('admin/dashboard/', api_views.admin_dashboard_api, name='api_admin_dashboard'),
    path('admin/stats/', api_views.admin_stats_api, name='api_admin_stats'),
    path('admin/users/', api_views.UserListView.as_view(), name='api_admin_users'),
    path('admin/users/create/', api_views.admin_create_user_api, name='api_admin_create_user'),
    path('admin/users/<int:user_id>/update/', api_views.admin_update_user_api, name='api_admin_update_user'),
    path('admin/users/<int:user_id>/delete/', api_views.admin_delete_user_api, name='api_admin_delete_user'),
    path('admin/users/<int:user_id>/toggle-status/', api_views.admin_toggle_user_status_api, name='api_admin_toggle_user_status'),
    path('admin/vendors/<int:vendor_id>/approve/', api_views.admin_approve_vendor_api, name='api_admin_approve_vendor'),
    path('admin/vendors/<int:vendor_id>/reject/', api_views.admin_reject_vendor_api, name='api_admin_reject_vendor'),
    
    # Order Management APIs
    path('', include('accounts.order_urls')),
    

    
    # Messaging APIs
    path('messaging/', include('accounts.message_urls')),
    
    # Notification APIs
    path('notifications/', notification_views.NotificationListView.as_view(), name='api_notifications'),
    path('notifications/<int:notification_id>/read/', notification_views.mark_notification_read, name='api_mark_notification_read'),
    path('notifications/mark-all-read/', notification_views.mark_all_notifications_read, name='api_mark_all_notifications_read'),
    path('notifications/count/', notification_views.notification_count, name='api_notification_count'),
    path('notifications/status/', api_views.notification_status_api, name='api_notification_status'),
    
    # Slider APIs
    path('sliders/', api_views.get_sliders_api, name='api_get_sliders'),
    
    # Vendor Notifications API
    path('vendor-notifications/', api_views.vendor_notifications_api, name='api_vendor_notifications'),
    
    # FCM Token Registration
    path('register-fcm-token/', api_views.register_fcm_token_api, name='api_register_fcm_token'),
    
    # Token refresh
    path('refresh-token/', refresh_token_api, name='api_refresh_token'),
    
    # Test FCM Notification
    path('test-fcm-notification/', api_views.test_fcm_notification_api, name='api_test_fcm_notification'),
    
    # Test Auto-Open Notification
    path('notifications/test-auto-open/', notification_views.test_auto_open_notification, name='api_test_auto_open_notification'),
    
    # Real-time notification check
    path('notifications/check/', check_notifications, name='api_check_notifications'),
    
    # Cross-domain message broadcasting
    path('broadcast/', broadcast_message, name='api_broadcast_message'),
    
    # Featured packages API
    path('featured-packages/', api_views.get_featured_packages_api, name='api_get_featured_packages'),
    path('featured-packages/purchase/', api_views.purchase_featured_package_api, name='api_purchase_featured_package'),
    path('products/<int:product_id>/featured-info/', api_views.get_product_featured_info_api, name='api_get_product_featured_info'),
    path('products/<int:product_id>/reschedule-featured/', api_views.reschedule_featured_package_api, name='api_reschedule_featured_package'),
    
    # Referral API
    path('validate-referral-code/', api_views.validate_referral_code_api, name='api_validate_referral_code'),
]
