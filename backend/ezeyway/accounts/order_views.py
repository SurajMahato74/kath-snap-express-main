from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
from .order_models import (
    Order, OrderItem, DeliveryRider, OrderDelivery, OrderStatusHistory,
    PaymentTransaction, OrderReview, OrderRefund, OrderNotification
)
from .order_serializers import (
    OrderSerializer, CreateOrderSerializer, UpdateOrderStatusSerializer,
    OrderReviewSerializer, OrderRefundSerializer, DeliveryRiderSerializer,
    OrderDeliverySerializer
)
from .models import CustomUser, VendorProfile
from .consumers import send_vendor_notification
from .notification_utils import send_order_status_notifications, send_payment_notification, send_refund_notification

def calculate_delivery_fee(order):
    """Calculate delivery fee for an order based on product settings"""
    calculated_fee = 0
    has_free_delivery = False
    
    for item in order.items.all():
        product = item.product
        
        # Check if any item has free delivery
        if product.free_delivery:
            has_free_delivery = True
            break
        
        # Check if product has custom delivery fee
        if product.custom_delivery_fee_enabled and product.custom_delivery_fee:
            calculated_fee = max(calculated_fee, float(product.custom_delivery_fee))
    
    if has_free_delivery:
        return 0
    elif calculated_fee > 0:
        return calculated_fee
    else:
        # Use vendor's default delivery fee or 0
        return float(order.vendor.delivery_fee or 0)

# Customer Order Views
class CustomerOrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = PageNumberPagination
    
    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user).order_by('-created_at')
    
    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except Exception:
            # Return empty page if pagination fails
            return Response({
                'count': 0,
                'next': None,
                'previous': None,
                'results': []
            })

class CustomerOrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_order_api(request):
    """Create new orders (separate orders for each vendor)"""
    serializer = CreateOrderSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        # Get all created orders by modifying the serializer temporarily
        items_data = request.data.get('items', [])
        customer = request.user
        
        # Group items by vendor to get all orders that will be created
        vendor_items = {}
        for item_data in items_data:
            from .models import Product
            product = Product.objects.get(id=item_data['product_id'])
            vendor_id = product.vendor.id
            if vendor_id not in vendor_items:
                vendor_items[vendor_id] = product.vendor
        
        # Create the orders using the serializer
        first_order = serializer.save()
        
        # Get all orders created for this customer in the last minute (to catch all related orders)
        from django.utils import timezone
        from datetime import timedelta
        recent_orders = Order.objects.filter(
            customer=customer,
            created_at__gte=timezone.now() - timedelta(minutes=1)
        ).order_by('-created_at')
        
        # Filter to only orders from the vendors we're creating orders for
        created_orders = []
        for order in recent_orders:
            if order.vendor.id in vendor_items.keys():
                created_orders.append(order)
                # Send notifications for each order
                send_order_status_notifications(order, 'pending')
                print(f"Order created: {order.id} for vendor: {order.vendor.business_name}")
        
        # Limit to the number of vendors we expect
        created_orders = created_orders[:len(vendor_items)]
        
        return Response({
            'message': f'{len(created_orders)} order(s) created successfully',
            'orders': [OrderSerializer(order, context={'request': request}).data for order in created_orders],
            'total_orders': len(created_orders),
            'vendors': [order.vendor.business_name for order in created_orders]
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def cancel_order_api(request, order_id):
    """Cancel an order"""
    try:
        order = Order.objects.get(id=order_id, customer=request.user)
        
        if not order.can_be_cancelled:
            return Response({
                'error': 'Order cannot be cancelled at this stage'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        cancellation_reason = request.data.get('reason', 'Cancelled by customer')
        
        # Update order status
        order.status = 'cancelled'
        order.cancelled_at = timezone.now()
        order.cancellation_reason = cancellation_reason
        order.save()
        
        # Create status history
        OrderStatusHistory.objects.create(
            order=order,
            status='cancelled',
            changed_by=request.user,
            notes=cancellation_reason
        )
        
        # Restore product quantities
        for item in order.items.all():
            product = item.product
            product.quantity += item.quantity
            product.save()
        
        # Send comprehensive order status notifications
        send_order_status_notifications(order, 'cancelled')
        
        # Send auto-open FCM notification to vendor about cancellation
        if order.vendor.fcm_token:
            from .firebase_init import send_data_only_message
            send_data_only_message(
                token=order.vendor.fcm_token,
                data={
                    "autoOpen": "true",
                    "orderId": str(order.id),
                    "orderNumber": order.order_number,
                    "status": "cancelled",
                    "action": "orderCancelled",
                    "forceOpen": "true"
                }
            )
        
        return Response({
            'message': 'Order cancelled successfully',
            'order': OrderSerializer(order, context={'request': request}).data
        })
        
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)


# Admin Views
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def admin_order_stats_api(request):
    """Get order statistics for admin dashboard"""
    if not request.user.is_superuser:
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    stats = {
        'total_orders': Order.objects.count(),
        'today_orders': Order.objects.filter(created_at__date=today).count(),
        'week_orders': Order.objects.filter(created_at__date__gte=week_ago).count(),
        'month_orders': Order.objects.filter(created_at__date__gte=month_ago).count(),
        
        'pending_orders': Order.objects.filter(status='pending').count(),
        'confirmed_orders': Order.objects.filter(status='confirmed').count(),
        'delivered_orders': Order.objects.filter(status='delivered').count(),
        'cancelled_orders': Order.objects.filter(status='cancelled').count(),
        
        'total_revenue': Order.objects.filter(
            status='delivered', payment_status='paid'
        ).aggregate(total=Sum('total_amount'))['total'] or 0,
        
        'pending_refunds': OrderRefund.objects.filter(status='requested').count(),
        'average_order_value': Order.objects.filter(
            status='delivered'
        ).aggregate(avg=Avg('total_amount'))['avg'] or 0,
    }
    
    return Response(stats)

class AdminOrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if not self.request.user.is_superuser:
            return Order.objects.none()
        
        queryset = Order.objects.all()
        
        # Filters
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        payment_status = self.request.query_params.get('payment_status')
        if payment_status:
            queryset = queryset.filter(payment_status=payment_status)
        
        vendor_id = self.request.query_params.get('vendor_id')
        if vendor_id:
            queryset = queryset.filter(vendor_id=vendor_id)
        
        customer_id = self.request.query_params.get('customer_id')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        
        return queryset.order_by('-created_at')

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def admin_process_refund_api(request, refund_id):
    """Process a refund request (admin only)"""
    if not request.user.is_superuser:
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

    try:
        refund = OrderRefund.objects.get(id=refund_id)
    except OrderRefund.DoesNotExist:
        return Response({'error': 'Refund not found'}, status=status.HTTP_404_NOT_FOUND)

    action = request.data.get('action')  # 'approve' or 'reject'
    admin_notes = request.data.get('admin_notes', '')
    approved_amount = request.data.get('approved_amount')

    if action == 'approve':
        refund.status = 'approved'
        refund.approved_at = timezone.now()
        refund.approved_amount = approved_amount or refund.requested_amount
        refund.admin_notes = admin_notes
        refund.processed_by = request.user
        refund.save()

        message = 'Refund approved'

    elif action == 'process':
        refund.status = 'processed'
        refund.processed_at = timezone.now()
        refund.admin_notes = admin_notes
        refund.processed_by = request.user
        refund.save()

        # Create payment transaction for refund
        PaymentTransaction.objects.create(
            order=refund.order,
            transaction_type='refund',
            status='completed',
            amount=refund.approved_amount or refund.requested_amount,
            payment_method=refund.order.payment_method,
            notes=f'Refund processed: {admin_notes}'
        )

        message = 'Refund processed - money transferred'

    elif action == 'complete':
        refund.status = 'completed'
        refund.completed_at = timezone.now()
        refund.admin_notes = admin_notes
        refund.save()

        # Update order payment status
        refund.order.payment_status = 'refunded'
        refund.order.save()

        message = 'Refund completed'

    elif action == 'reject':
        refund.status = 'rejected'
        refund.admin_notes = admin_notes
        refund.processed_by = request.user
        refund.save()

        message = 'Refund request rejected'

    else:
        return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

    # Send refund notification
    send_refund_notification(refund, action)

    return Response({
        'message': message,
        'refund': OrderRefundSerializer(refund).data
    })

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def vendor_process_refund_api(request, refund_id):
    """Process a refund request (vendor only)"""
    try:
        refund = OrderRefund.objects.get(id=refund_id)

        # Check if user is vendor of the order
        try:
            vendor_profile = VendorProfile.objects.get(user=request.user, is_approved=True)
            if refund.order.vendor != vendor_profile:
                return Response({'error': 'Access denied - not your order'}, status=status.HTTP_403_FORBIDDEN)
        except VendorProfile.DoesNotExist:
            return Response({'error': 'Vendor profile not found'}, status=status.HTTP_403_FORBIDDEN)

    except OrderRefund.DoesNotExist:
        return Response({'error': 'Refund not found'}, status=status.HTTP_404_NOT_FOUND)

    action = request.data.get('action')  # 'approve' or 'reject'
    admin_notes = request.data.get('admin_notes', '')
    approved_amount = request.data.get('approved_amount')

    if action == 'approve':
        refund.status = 'approved'
        refund.approved_at = timezone.now()
        refund.approved_amount = approved_amount or refund.requested_amount
        refund.admin_notes = admin_notes
        refund.processed_by = request.user
        refund.save()

        message = 'Refund approved'

    elif action == 'process':
        refund.status = 'processed'
        refund.processed_at = timezone.now()
        refund.admin_notes = admin_notes
        refund.processed_by = request.user
        refund.save()

        # Create payment transaction for refund
        PaymentTransaction.objects.create(
            order=refund.order,
            transaction_type='refund',
            status='completed',
            amount=refund.approved_amount or refund.requested_amount,
            payment_method=refund.order.payment_method,
            notes=f'Refund processed: {admin_notes}'
        )

        message = 'Refund processed - money transferred'

    elif action == 'complete':
        refund.status = 'completed'
        refund.completed_at = timezone.now()
        refund.admin_notes = admin_notes
        refund.save()

        # Update order payment status
        refund.order.payment_status = 'refunded'
        refund.order.save()

        message = 'Refund completed'

    elif action == 'reject':
        refund.status = 'rejected'
        refund.admin_notes = admin_notes
        refund.processed_by = request.user
        refund.save()

        message = 'Refund request rejected'

    else:
        return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

    # Send refund notification
    send_refund_notification(refund, action)

    return Response({
        'message': message,
        'refund': OrderRefundSerializer(refund).data
    })

# Delivery Rider Views
class DeliveryRiderListView(generics.ListCreateAPIView):
    serializer_class = DeliveryRiderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if not self.request.user.is_superuser:
            return DeliveryRider.objects.none()
        return DeliveryRider.objects.all().order_by('name')

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def update_delivery_location_api(request, delivery_id):
    """Update delivery rider location"""
    try:
        delivery = OrderDelivery.objects.get(id=delivery_id)
        
        # Only rider or admin can update location
        if not (request.user.is_superuser or request.user == delivery.rider.user):
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')
        
        if not latitude or not longitude:
            return Response({'error': 'Latitude and longitude required'}, status=status.HTTP_400_BAD_REQUEST)
        
        delivery.current_latitude = latitude
        delivery.current_longitude = longitude
        delivery.save()
        
        # Update rider's current location
        delivery.rider.current_latitude = latitude
        delivery.rider.current_longitude = longitude
        delivery.rider.last_location_update = timezone.now()
        delivery.rider.save()
        
        return Response({
            'message': 'Location updated successfully',
            'delivery': OrderDeliverySerializer(delivery).data
        })
        
    except OrderDelivery.DoesNotExist:
        return Response({'error': 'Delivery not found'}, status=status.HTTP_404_NOT_FOUND)

# Vendor-specific order endpoints
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def vendor_pending_orders_api(request):
    """Get pending orders for vendor"""
    try:
        vendor_profile = VendorProfile.objects.get(user=request.user, is_approved=True)
        
        # Get pending orders for this vendor
        orders = Order.objects.filter(
            vendor=vendor_profile, 
            status='pending'
        ).order_by('-created_at')
        
        serializer = OrderSerializer(orders, many=True, context={'request': request})
        return Response(serializer.data)
        
    except VendorProfile.DoesNotExist:
        return Response({'error': 'Vendor profile not found or not approved'}, status=status.HTTP_403_FORBIDDEN)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def vendor_accept_order_api(request, order_id):
    """Accept an order (vendor only)"""
    print(f"🔥 VENDOR ACCEPT ORDER API CALLED - Order ID: {order_id}, User: {request.user}")
    
    try:
        vendor_profile = VendorProfile.objects.get(user=request.user)
        print(f"🔥 Found vendor profile: ID={vendor_profile.id}, Name={vendor_profile.business_name}")
        
        # Check if order exists at all
        try:
            order_check = Order.objects.get(id=order_id)
            print(f"🔥 Order {order_id} exists - Status: {order_check.status}, Vendor ID: {order_check.vendor.id}, Vendor: {order_check.vendor.business_name}")
        except Order.DoesNotExist:
            print(f"🔥 Order {order_id} does not exist in database")
            return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if order belongs to this vendor
        if order_check.vendor != vendor_profile:
            print(f"🔥 Order belongs to different vendor: {order_check.vendor.business_name}")
            return Response({
                'error': 'This order does not belong to your vendor profile',
                'details': f'Order belongs to {order_check.vendor.business_name}'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Additional check: Don't allow vendors to accept their own orders
        if order_check.customer == request.user:
            print(f"🔥 Vendor trying to accept their own order")
            return Response({'error': 'Cannot accept your own order'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check order status
        if order_check.status != 'pending':
            print(f"🔥 Order status is {order_check.status}, not pending")
            return Response({'error': f'Order status is {order_check.status}, cannot accept'}, status=status.HTTP_400_BAD_REQUEST)
        
        order = order_check
        
        # Get charge for this order amount
        from .models import ChargeRate, VendorWallet
        
        # Find matching charge rate
        charge_amount = 0
        charge_rates = ChargeRate.objects.all().order_by('min_amount')
        for rate in charge_rates:
            if order.total_amount >= rate.min_amount:
                if rate.max_amount is None or order.total_amount <= rate.max_amount:
                    charge_amount = rate.charge
                    break
        
        # Check if vendor has sufficient wallet balance
        wallet, created = VendorWallet.objects.get_or_create(vendor=vendor_profile)
        
        if wallet.balance < charge_amount:
            return Response({
                'error': f'Insufficient wallet balance. Required: ₹{charge_amount}, Available: ₹{wallet.balance}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Deduct charge from vendor wallet
        if charge_amount > 0:
            success = wallet.deduct_commission(
                amount=charge_amount,
                order_amount=order.total_amount,
                description=f"Order confirmation charge - Order #{order.order_number}"
            )
            
            if not success:
                return Response({
                    'error': 'Failed to deduct charge from wallet'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update order status
        order.status = 'confirmed'
        order.confirmed_at = timezone.now()
        order.save()
        
        # Create status history
        OrderStatusHistory.objects.create(
            order=order,
            status='confirmed',
            changed_by=request.user,
            notes=f'Order accepted by vendor. Charge deducted: ₹{charge_amount}'
        )
        
        # Send comprehensive order status notifications
        send_order_status_notifications(order, 'confirmed', 'pending')
        
        return Response({
            'message': f'Order accepted successfully. Charge of ₹{charge_amount} deducted from wallet.',
            'charge_deducted': float(charge_amount),
            'remaining_balance': float(wallet.balance),
            'order': OrderSerializer(order, context={'request': request}).data
        })
        
    except (VendorProfile.DoesNotExist, Order.DoesNotExist):
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def vendor_reject_order_api(request, order_id):
    """Reject an order (vendor only)"""
    
    try:
        vendor_profile = VendorProfile.objects.get(user=request.user)
        order = Order.objects.get(id=order_id, vendor=vendor_profile, status='pending')
        
        reason = request.data.get('reason', 'Rejected by vendor')
        
        # Update order status
        order.status = 'cancelled'
        order.cancelled_at = timezone.now()
        order.cancellation_reason = reason
        order.save()
        
        # Create status history
        OrderStatusHistory.objects.create(
            order=order,
            status='cancelled',
            changed_by=request.user,
            notes=reason
        )
        
        # Restore product quantities
        for item in order.items.all():
            product = item.product
            product.quantity += item.quantity
            product.save()
        
        # Send comprehensive order status notifications
        send_order_status_notifications(order, 'cancelled', 'pending')
        
        return Response({
            'message': 'Order rejected successfully',
            'order': OrderSerializer(order, context={'request': request}).data
        })
        
    except (VendorProfile.DoesNotExist, Order.DoesNotExist):
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def upload_refund_document_api(request, refund_id):
    """Upload refund completion document"""
    try:
        refund = OrderRefund.objects.get(id=refund_id)
        
        # Check permission
        has_permission = request.user.is_superuser or refund.customer == request.user
        try:
            vendor_profile = VendorProfile.objects.get(user=request.user, is_approved=True)
            has_permission = refund.order.vendor == vendor_profile
        except VendorProfile.DoesNotExist:
            pass
        
        if not has_permission:
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # Handle file upload
        if 'document' in request.FILES:
            import os
            from django.conf import settings
            from django.core.files.storage import default_storage
            
            file = request.FILES['document']
            
            # Create directory if it doesn't exist
            upload_dir = 'refund_documents'
            if not os.path.exists(os.path.join(settings.MEDIA_ROOT, upload_dir)):
                os.makedirs(os.path.join(settings.MEDIA_ROOT, upload_dir))
            
            # Generate unique filename
            import uuid
            file_extension = os.path.splitext(file.name)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(upload_dir, unique_filename)
            
            # Save file
            saved_path = default_storage.save(file_path, file)
            file_url = default_storage.url(saved_path)
            
            # Update evidence_photos with file info
            evidence_photos = refund.evidence_photos or []
            evidence_photos.append({
                'filename': file.name,
                'saved_filename': unique_filename,
                'file_path': saved_path,
                'file_url': file_url,
                'uploaded_by': request.user.username,
                'uploaded_at': timezone.now().isoformat(),
                'type': 'refund_document'
            })
            refund.evidence_photos = evidence_photos
            refund.save()
            
            return Response({
                'message': 'Document uploaded successfully',
                'refund': OrderRefundSerializer(refund).data
            })
        
        return Response({'error': 'No document provided'}, status=status.HTTP_400_BAD_REQUEST)
        
    except OrderRefund.DoesNotExist:
        return Response({'error': 'Refund not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_calculated_delivery_fee_api(request, order_id):
    """Get calculated delivery fee for an order"""
    try:
        vendor_profile = VendorProfile.objects.get(user=request.user)
        order = Order.objects.get(id=order_id, vendor=vendor_profile)
        
        calculated_fee = calculate_delivery_fee(order)
        
        return Response({
            'delivery_fee': calculated_fee,
            'order_id': order_id
        })
        
    except (VendorProfile.DoesNotExist, Order.DoesNotExist):
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def debug_vendor_orders_api(request):
    """Debug endpoint to show vendor order mapping"""
    try:
        vendor_profile = VendorProfile.objects.get(user=request.user)
        
        # Get all orders for this vendor
        vendor_orders = Order.objects.filter(vendor=vendor_profile)
        
        # Get all orders in system for comparison
        all_orders = Order.objects.all()[:10]  # Limit to 10 for debugging
        
        return Response({
            'current_user': request.user.username,
            'vendor_profile_id': vendor_profile.id,
            'vendor_business_name': vendor_profile.business_name,
            'vendor_orders': [
                {
                    'id': order.id,
                    'status': order.status,
                    'customer': order.customer.username,
                    'total': float(order.total_amount)
                } for order in vendor_orders
            ],
            'all_orders_sample': [
                {
                    'id': order.id,
                    'vendor_id': order.vendor.id,
                    'vendor_name': order.vendor.business_name,
                    'customer': order.customer.username,
                    'status': order.status
                } for order in all_orders
            ]
        })
        
    except VendorProfile.DoesNotExist:
        return Response({'error': 'No vendor profile found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_product_reviews_api(request, product_id):
    """Get aggregate reviews for a specific product"""
    try:
        from .models import Product, OrderItem
        from django.db.models import Avg, Count
        
        # Get the product
        product = get_object_or_404(Product, id=product_id)
        
        # Get all orders containing this product that have reviews
        reviews = OrderReview.objects.filter(
            order__items__product=product,
            order__status='delivered'
        ).select_related('order', 'customer')
        
        # Calculate aggregate metrics using actual OrderReview fields
        aggregate_data = reviews.aggregate(
            avg_rating=Avg('overall_rating'),
            total_reviews=Count('id'),
            avg_quality=Avg('food_quality_rating'),
            avg_value=Avg('delivery_rating'),
            avg_service=Avg('vendor_rating')
        )

        # Get recent reviews
        recent_reviews = reviews.order_by('-created_at')[:5]

        # Format the response
        response_data = {
            'product_id': product_id,
            'product_name': product.name,
            'aggregate': {
                'average_rating': float(aggregate_data['avg_rating'] or 0),
                'total_reviews': aggregate_data['total_reviews'] or 0,
                'average_quality': float(aggregate_data['avg_quality'] or 0),
                'average_value': float(aggregate_data['avg_value'] or 0),
                'average_service': float(aggregate_data['avg_service'] or 0)
            },
            'recent_reviews': [{
                'rating': getattr(review, 'overall_rating', None),
                'comment': getattr(review, 'review_text', ''),
                'customer_name': review.customer.get_full_name() or review.customer.username,
                'created_at': review.created_at,
                'quality_rating': getattr(review, 'food_quality_rating', None),
                'value_rating': getattr(review, 'delivery_rating', None),
                'service_rating': getattr(review, 'vendor_rating', None)
            } for review in recent_reviews]
        }
        
        return Response(response_data)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to get product reviews: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def get_vendor_reviews_api(request, vendor_id):
    """Get aggregate reviews for a vendor's products"""
    try:
        from django.db.models import Avg, Count
        vendor_profile = get_object_or_404(VendorProfile, id=vendor_id)
        
        # Get all reviews for this vendor's products
        reviews = OrderReview.objects.filter(
            order__vendor=vendor_profile,
            order__status='delivered'
        ).select_related('order', 'customer')
        
        # Calculate aggregate metrics using actual OrderReview fields
        aggregate_data = reviews.aggregate(
            avg_rating=Avg('overall_rating'),
            total_reviews=Count('id'),
            avg_quality=Avg('food_quality_rating'),
            avg_value=Avg('delivery_rating'),
            avg_service=Avg('vendor_rating')
        )

        # Get recent reviews
        recent_reviews = reviews.order_by('-created_at')[:5]

        # Format the response
        response_data = {
            'vendor_id': vendor_id,
            'vendor_name': vendor_profile.business_name,
            'aggregate': {
                'average_rating': float(aggregate_data['avg_rating'] or 0),
                'total_reviews': aggregate_data['total_reviews'] or 0,
                'average_quality': float(aggregate_data['avg_quality'] or 0),
                'average_value': float(aggregate_data['avg_value'] or 0),
                'average_service': float(aggregate_data['avg_service'] or 0)
            },
            'recent_reviews': [{
                'rating': getattr(review, 'overall_rating', None),
                'comment': getattr(review, 'review_text', ''),
                'customer_name': review.customer.get_full_name() or review.customer.username,
                'created_at': review.created_at,
                'quality_rating': getattr(review, 'food_quality_rating', None),
                'value_rating': getattr(review, 'delivery_rating', None),
                'service_rating': getattr(review, 'vendor_rating', None),
                'product_name': None
            } for review in recent_reviews]
        }
        
        return Response(response_data)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to get vendor reviews: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Debug endpoint
@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def test_order_endpoint(request):
    """Test endpoint to verify URL routing is working"""
    print(f"🔥 TEST ORDER ENDPOINT CALLED - Method: {request.method}, User: {request.user}")
    return Response({
        'message': 'Order URL routing is working!',
        'method': request.method,
        'user': str(request.user),
        'timestamp': timezone.now().isoformat()
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_order_exists_api(request, order_id):
    """Check if an order exists and show details"""
    try:
        order = Order.objects.get(id=order_id)
        return Response({
            'exists': True,
            'order_id': order.id,
            'status': order.status,
            'vendor_id': order.vendor.id,
            'vendor_name': order.vendor.business_name,
            'customer': order.customer.username,
            'total_amount': float(order.total_amount),
            'created_at': order.created_at.isoformat()
        })
    except Order.DoesNotExist:
        # Show all orders to help debug
        all_orders = Order.objects.all().values('id', 'status', 'vendor__business_name', 'customer__username')[:10]
        return Response({
            'exists': False,
            'order_id': order_id,
            'message': f'Order {order_id} not found',
            'available_orders': list(all_orders)
        })

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def ship_order_api(request, order_id):
    """Ship an order with delivery details (vendor only)"""
    try:
        vendor_profile = VendorProfile.objects.get(user=request.user, is_approved=True)
        order = Order.objects.get(id=order_id, vendor=vendor_profile, status='confirmed')

        # Validate required fields
        delivery_boy_phone = request.data.get('delivery_boy_phone')
        vehicle_number = request.data.get('vehicle_number')
        vehicle_color = request.data.get('vehicle_color')
        estimated_delivery_time = request.data.get('estimated_delivery_time')
        delivery_fee = request.data.get('delivery_fee', 0)

        if not delivery_boy_phone:
            return Response({'error': 'Delivery boy phone is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not vehicle_number:
            return Response({'error': 'Vehicle number is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not vehicle_color:
            return Response({'error': 'Vehicle color is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not estimated_delivery_time:
            return Response({'error': 'Estimated delivery time is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Update order with delivery details
        order.status = 'out_for_delivery'
        order.delivery_boy_phone = delivery_boy_phone
        order.vehicle_number = vehicle_number
        order.vehicle_color = vehicle_color
        order.estimated_delivery_time = estimated_delivery_time
        order.delivery_fee = delivery_fee
        order.out_for_delivery_at = timezone.now()
        order.notes = request.data.get('notes', 'Order shipped with delivery details')
        order.save()

        # Create status history
        OrderStatusHistory.objects.create(
            order=order,
            status='out_for_delivery',
            changed_by=request.user,
            notes=f'Order shipped - Delivery boy: {delivery_boy_phone}, Vehicle: {vehicle_number} ({vehicle_color})'
        )

        # Send comprehensive order status notifications
        send_order_status_notifications(order, 'out_for_delivery', 'confirmed')

        return Response({
            'message': 'Order shipped successfully',
            'order': OrderSerializer(order, context={'request': request}).data
        })

    except VendorProfile.DoesNotExist:
        return Response({'error': 'Vendor profile not found or not approved'}, status=status.HTTP_403_FORBIDDEN)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found or not in confirmed status'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def quick_update_order_status_api(request, order_id):
    """Quick order status update without complex validation - for debugging"""
    print(f"🔥 QUICK UPDATE ORDER STATUS - Order ID: {order_id}, User: {request.user}")
    print(f"🔥 Request data: {request.data}")

    try:
        # Check if order exists
        order = Order.objects.get(id=order_id)
        print(f"🔥 Order found: {order.order_number}, Status: {order.status}")

        # Check vendor permission (allow superuser override)
        if not request.user.is_superuser:
            try:
                vendor_profile = VendorProfile.objects.get(user=request.user)
                if order.vendor != vendor_profile:
                    return Response({'error': 'Order does not belong to your vendor profile'}, status=status.HTTP_403_FORBIDDEN)
            except VendorProfile.DoesNotExist:
                return Response({'error': 'Vendor profile not found'}, status=status.HTTP_403_FORBIDDEN)

        # Update order directly without serializer validation
        new_status = request.data.get('status')
        if new_status:
            old_status = order.status
            order.status = new_status

            # Update delivery info if provided
            if request.data.get('delivery_boy_phone'):
                order.delivery_boy_phone = request.data.get('delivery_boy_phone')
            if request.data.get('vehicle_number'):
                order.vehicle_number = request.data.get('vehicle_number')
            if request.data.get('vehicle_color'):
                order.vehicle_color = request.data.get('vehicle_color')
            if request.data.get('estimated_delivery_time'):
                order.estimated_delivery_time = request.data.get('estimated_delivery_time')
            if request.data.get('delivery_fee') is not None:
                order.delivery_fee = request.data.get('delivery_fee')
            if request.data.get('notes'):
                order.notes = request.data.get('notes')

            # Update timestamps
            if new_status == 'out_for_delivery':
                order.out_for_delivery_at = timezone.now()
            elif new_status == 'delivered':
                order.delivered_at = timezone.now()
            elif new_status == 'confirmed':
                order.confirmed_at = timezone.now()

            order.save()
            print(f"🔥 Order updated successfully: {old_status} -> {new_status}")

            # Create status history
            OrderStatusHistory.objects.create(
                order=order,
                status=new_status,
                changed_by=request.user,
                notes=request.data.get('notes', f'Status updated to {new_status}')
            )

            return Response({
                'success': True,
                'message': f'Order status updated to {new_status}',
                'order': {
                    'id': order.id,
                    'order_number': order.order_number,
                    'status': order.status,
                    'delivery_boy_phone': order.delivery_boy_phone,
                    'vehicle_number': order.vehicle_number,
                    'vehicle_color': order.vehicle_color,
                    'estimated_delivery_time': order.estimated_delivery_time,
                    'delivery_fee': float(order.delivery_fee or 0),
                    'notes': order.notes
                }
            })
        else:
            return Response({'error': 'Status is required'}, status=status.HTTP_400_BAD_REQUEST)

    except Order.DoesNotExist:
        print(f"🔥 Order {order_id} not found")
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"🔥 Error: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
