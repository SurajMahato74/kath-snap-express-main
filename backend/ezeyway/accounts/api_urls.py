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

    # FCM Token Registration
    path('register-fcm-token/', api_views.register_fcm_token_api, name='register_fcm_token'),

    # Vendor Profiles
    path('vendor-profiles/', api_views.VendorProfileListCreateView.as_view(), name='vendor_profiles'),

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

    # Vendor Orders (direct endpoint for frontend compatibility)
    path('vendor/orders/', include('accounts.order_urls')),

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

    # Categories and Products
    path('categories/', api_views.categories_api, name='categories'),
    path('sliders/', api_views.get_sliders_api, name='sliders'),
    path('search/products/', api_views.search_products_api, name='search_products'),

    # Test endpoints
    path('test/', api_views.test_api, name='test'),
    path('health/', api_views.health_check, name='health'),
]
