from django.urls import path
from . import api_views

urlpatterns = [
    # Authentication
    path('register/', api_views.register_api, name='register'),
    path('login/', api_views.login_api, name='login'),
    path('logout/', api_views.logout_api, name='logout'),
    path('profile/', api_views.profile_api, name='profile'),
    path('setup-password/', api_views.setup_password_api, name='setup_password'),
    
    # FCM Token Registration
    path('register-fcm-token/', api_views.register_fcm_token_api, name='register_fcm_token'),
    
    # Order Management
    path('orders/vendor/pending/', api_views.vendor_pending_orders_api, name='vendor_pending_orders'),
    path('orders/<int:order_id>/accept/', api_views.accept_order_api, name='accept_order'),
    path('orders/<int:order_id>/reject/', api_views.reject_order_api, name='reject_order'),
    
    # Vendor Status
    path('vendor/toggle-status/', api_views.toggle_vendor_status_api, name='toggle_vendor_status'),
    path('vendor/status/', api_views.vendor_status_api, name='vendor_status'),
    
    # Notifications
    path('notifications/', api_views.notification_status_api, name='notifications'),

    # Categories and Products
    path('categories/', api_views.categories_api, name='categories'),
    path('sliders/', api_views.sliders_api, name='sliders'),
    path('search/products/', api_views.search_products_api, name='search_products'),

    # Test endpoints
    path('test/', api_views.test_api, name='test'),
    path('health/', api_views.health_check, name='health'),
]
