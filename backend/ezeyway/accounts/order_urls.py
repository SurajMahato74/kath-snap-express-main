from django.urls import path
from . import order_views, customer_order_views

urlpatterns = [
    # Customer Order URLs
    path('', order_views.CustomerOrderListView.as_view(), name='customer_orders'),
    path('<int:pk>/', order_views.CustomerOrderDetailView.as_view(), name='customer_order_detail'),
    path('create/', order_views.create_order_api, name='create_order'),
    path('<int:order_id>/cancel/', order_views.cancel_order_api, name='cancel_order'),
    path('<int:order_id>/status/', customer_order_views.customer_update_order_status_api, name='customer_update_order_status'),
    
    # Vendor Order URLs
    path('vendor/orders/', order_views.VendorOrderListView.as_view(), name='vendor_orders'),
    path('vendor/orders/<int:order_id>/status/', order_views.update_order_status_api, name='update_order_status'),
    path('orders/vendor/pending/', order_views.vendor_pending_orders_api, name='vendor_pending_orders'),

    # Additional vendor order endpoints for frontend compatibility
    path('vendor/pending/', order_views.vendor_pending_orders_api, name='vendor_pending_orders_alt'),
    path('vendor/orders/', order_views.VendorOrderListView.as_view(), name='vendor_orders_alt'),
    
    # Order Accept/Reject endpoints - CRITICAL: These must be accessible
    # Multiple patterns to ensure the endpoint is accessible
    path('orders/<int:order_id>/accept/', order_views.vendor_accept_order_api, name='vendor_accept_order'),
    path('orders/<int:order_id>/reject/', order_views.vendor_reject_order_api, name='vendor_reject_order'),
    
    # Alternative patterns for accept/reject (in case of routing issues)
    path('vendor/orders/<int:order_id>/accept/', order_views.vendor_accept_order_api, name='vendor_accept_order_alt'),
    path('vendor/orders/<int:order_id>/reject/', order_views.vendor_reject_order_api, name='vendor_reject_order_alt'),
    
    # Debug endpoint to test URL routing
    path('orders/test/', order_views.test_order_endpoint, name='test_order_endpoint'),
    path('orders/debug/', order_views.debug_vendor_orders_api, name='debug_vendor_orders'),
    path('orders/<int:order_id>/check/', order_views.check_order_exists_api, name='check_order_exists'),
    path('orders/<int:order_id>/quick-update/', order_views.quick_update_order_status_api, name='quick_update_order_status'),
    
    # Get calculated delivery fee for an order
    path('orders/<int:order_id>/delivery-fee/', order_views.get_calculated_delivery_fee_api, name='get_calculated_delivery_fee'),
    
    # Review URLs
    path('orders/<int:order_id>/review/', order_views.create_review_api, name='create_review'),
    path('products/<int:product_id>/reviews/', order_views.get_product_reviews_api, name='get_product_reviews'),
    path('vendors/<int:vendor_id>/reviews/', order_views.get_vendor_reviews_api, name='get_vendor_reviews'),
    
    # Refund URLs
    path('orders/<int:order_id>/refund/', order_views.request_refund_api, name='request_refund'),
    path('orders/<int:order_id>/return/', order_views.request_return_api, name='request_return'),
    path('refunds/<int:refund_id>/appeal/', order_views.appeal_refund_api, name='appeal_refund'),
    path('refunds/<int:refund_id>/upload-document/', order_views.upload_refund_document_api, name='upload_refund_document'),
    path('refunds/<int:refund_id>/mark-received/', customer_order_views.mark_refund_received_api, name='mark_refund_received'),
    path('refunds/<int:refund_id>/contact-support/', customer_order_views.contact_support_refund_api, name='contact_support_refund'),

    # Admin Order URLs
    path('admin/orders/', order_views.AdminOrderListView.as_view(), name='admin_orders'),
    path('admin/orders/stats/', order_views.admin_order_stats_api, name='admin_order_stats'),
    path('admin/refunds/<int:refund_id>/process/', order_views.admin_process_refund_api, name='admin_process_refund'),
    
    # Vendor Refund URLs
    path('vendor/refunds/<int:refund_id>/process/', order_views.vendor_process_refund_api, name='vendor_process_refund'),
    
    # Delivery URLs
    path('delivery/riders/', order_views.DeliveryRiderListView.as_view(), name='delivery_riders'),
    path('delivery/<int:delivery_id>/location/', order_views.update_delivery_location_api, name='update_delivery_location'),

    # Ship order endpoint
    path('orders/<int:order_id>/ship/', order_views.ship_order_api, name='ship_order'),
]