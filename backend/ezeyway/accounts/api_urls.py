from django.urls import path, include
from . import api_views
from . import order_views

urlpatterns = [
    # Authentication
    path('register/', api_views.register_api, name='register'),
    path('login/', api_views.login_api, name='login'),
    path('logout/', api_views.logout_api, name='logout'),
    path('profile/', api_views.profile_api, name='profile'),
    path('setup-password/', api_views.setup_password_api, name='setup_password'),
    path('auth/google/', api_views.google_oauth_api, name='google_oauth'),
    path('auth/facebook/', api_views.facebook_oauth_api, name='facebook_oauth'),
    path('agree-privacy-policy/', api_views.agree_privacy_policy_api, name='agree_privacy_policy'),
    path('check-password-setup/', api_views.check_password_setup_api, name='check_password_setup'),

    # FCM Token Registration
    path('register-fcm-token/', api_views.register_fcm_token_api, name='register_fcm_token'),

    # Vendor Profiles
    path('vendor-profiles/', api_views.VendorProfileListCreateView.as_view(), name='vendor_profiles'),
    path('vendor-profiles/<int:pk>/', api_views.VendorProfileDetailView.as_view(), name='vendor_profile_detail'),
    path('vendor-profiles/<int:pk>/toggle-status/', api_views.vendor_toggle_status_api, name='vendor_toggle_status_detail'),

    # Order Management
    path('orders/', include('accounts.order_urls')),

    # Vendor Status
    path('vendor/toggle-status/', api_views.toggle_vendor_status_api, name='toggle_vendor_status'),
    path('vendor/status/', api_views.vendor_status_api, name='vendor_status'),

    # Notifications
    path('notifications/', api_views.notification_status_api, name='notifications'),

    # Messaging
    path('messaging/', include('accounts.message_urls')),

    # Vendor Notifications
    path('vendor-notifications/', include('accounts.notification_urls')),

    # Vendor Wallet
    path('vendor-wallet/', api_views.vendor_wallet_api, name='vendor_wallet'),
    path('wallet/transactions/', api_views.wallet_transactions_api, name='wallet_transactions'),

    # Vendor Orders (direct endpoint for frontend compatibility)
    path('vendor/orders/', include('accounts.order_urls')),

    # Web Push Notifications
    path('send-web-push-notification/', api_views.send_web_push_notification_api, name='send_web_push_notification'),

    # Favorites
    path('favorites/', api_views.UserFavoriteListView.as_view(), name='favorites'),
    path('favorites/toggle/', api_views.toggle_favorite_api, name='toggle_favorite'),

    # Cart Management
    path('cart/', api_views.get_cart_api, name='get_cart'),
    path('cart/add/', api_views.add_to_cart_api, name='add_to_cart'),
    path('cart/item/<int:item_id>/update/', api_views.update_cart_item_api, name='update_cart_item'),
    path('cart/item/<int:item_id>/remove/', api_views.remove_from_cart_api, name='remove_from_cart'),
    path('cart/clear/', api_views.clear_cart_api, name='clear_cart'),

    # Search Vendors
    path('search/vendors/', api_views.CustomerVendorSearchView.as_view(), name='search_vendors'),
    path('vendors/<int:vendor_id>/', api_views.CustomerVendorProfileView.as_view(), name='customer_vendor_profile'),

    # Review URLs (direct access for frontend compatibility)
    path('products/<int:product_id>/reviews/', order_views.get_product_reviews_api, name='get_product_reviews_direct'),
    path('vendors/<int:vendor_id>/reviews/', order_views.get_vendor_reviews_api, name='get_vendor_reviews_direct'),

    # Categories and Products
    path('categories/', api_views.categories_api, name='categories'),
    path('categories/<str:category_name>/subcategories/', api_views.get_subcategories_api, name='get_subcategories'),
    path('categories/parameters/', api_views.get_category_parameters_compat_api, name='get_category_parameters_compat'),
    path('accounts/categories/parameters/', api_views.get_category_parameters_compat_api, name='accounts_category_parameters'),
    path('products/', api_views.ProductListCreateView.as_view(), name='products'),
    path('products/<int:pk>/', api_views.ProductDetailView.as_view(), name='product_detail'),
    path('products/<int:product_id>/images/<int:image_id>/', api_views.delete_product_image, name='delete_product_image'),
    path('delivery-radius/', api_views.get_delivery_radius_api, name='delivery_radius'),
    path('sliders/', api_views.get_sliders_api, name='sliders'),
    path('search/products/', api_views.search_products_api, name='search_products'),

    # Test endpoints
    path('test/', api_views.test_api, name='test'),
    path('health/', api_views.health_check, name='health'),
]
