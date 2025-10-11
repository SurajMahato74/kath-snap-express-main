from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
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

# Customer Order Views
class CustomerOrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user).order_by('-created_at')

class CustomerOrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_order_api(request):
    """Create a new order"""
    serializer = CreateOrderSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        order = serializer.save()
        
        # Send comprehensive order status notifications
        send_order_status_notifications(order, 'pending')
        
        # Send auto-open FCM notification to vendor
        print(f"Checking vendor FCM token for order {order.id}")
        print(f"Vendor: {order.vendor.business_name}")
        print(f"FCM Token exists: {bool(order.vendor.fcm_token)}")
        
        if order.vendor.fcm_token:
            print(f"Sending auto-open FCM to: {order.vendor.fcm_token[:30]}...")
            from .firebase_init import send_data_only_message
            
            fcm_data = {
                "autoOpen": "true",
                "orderId": str(order.id),
                "orderNumber": order.order_number,
                "amount": str(order.total_amount),
                "action": "autoOpenOrder",
                "forceOpen": "true"
            }
            
            print(f"FCM Data: {fcm_data}")
            
            success = send_data_only_message(
                token=order.vendor.fcm_token,
                data=fcm_data
            )
            
            if success:
                print(f"Auto-open FCM sent successfully for order {order.id}")
            else:
                print(f"Failed to send auto-open FCM for order {order.id}")
        else:
            print(f"No FCM token found for vendor {order.vendor.business_name}")
        
        return Response({
            'message': 'Order created successfully',
            'order': OrderSerializer(order, context={'request': request}).data,
            'fcm_sent': bool(order.vendor.fcm_token)
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

# Vendor Order Views
class VendorOrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        if not self.request.user.is_vendor:
            return Order.objects.none()
        
        try:
            vendor_profile = VendorProfile.objects.get(user=self.request.user)
            queryset = Order.objects.filter(vendor=vendor_profile)
            
            # Filter by status
            status_filter = self.request.query_params.get('status')
            if status_filter:
                queryset = queryset.filter(status=status_filter)
            
            # Filter by date range
            date_from = self.request.query_params.get('date_from')
            date_to = self.request.query_params.get('date_to')
            if date_from:
                queryset = queryset.filter(created_at__date__gte=date_from)
            if date_to:
                queryset = queryset.filter(created_at__date__lte=date_to)
            
            return queryset.order_by('-created_at')
        except VendorProfile.DoesNotExist:
            return Order.objects.none()

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def update_order_status_api(request, order_id):
    """Update order status (vendor only)"""
    if not request.user.is_vendor:
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        vendor_profile = VendorProfile.objects.get(user=request.user)
        order = Order.objects.get(id=order_id, vendor=vendor_profile)
        
        serializer = UpdateOrderStatusSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        new_status = serializer.validated_data['status']
        notes = serializer.validated_data.get('notes', '')
        
        # Update order status
        old_status = order.status
        order.status = new_status
        
        # Update timestamps based on status
        if new_status == 'confirmed':
            order.confirmed_at = timezone.now()
        elif new_status == 'preparing':
            order.prepared_at = timezone.now()
        elif new_status == 'out_for_delivery':
            order.out_for_delivery_at = timezone.now()
            
            # Save delivery information
            order.delivery_boy_phone = serializer.validated_data.get('delivery_boy_phone')
            order.vehicle_number = serializer.validated_data.get('vehicle_number')
            order.vehicle_color = serializer.validated_data.get('vehicle_color')
            order.estimated_delivery_time = serializer.validated_data.get('estimated_delivery_time')
            
            # Update delivery fee if provided
            delivery_fee = serializer.validated_data.get('delivery_fee')
            if delivery_fee is not None:
                order.delivery_fee = delivery_fee
                # Do NOT update total_amount - delivery fee is separate from bill total
        elif new_status == 'delivered':
            order.delivered_at = timezone.now()
            if hasattr(order, 'delivery'):
                order.delivery.status = 'delivered'
                order.delivery.delivered_at = timezone.now()
                order.delivery.save()
        
        order.save()
        
        # Create status history
        OrderStatusHistory.objects.create(
            order=order,
            status=new_status,
            changed_by=request.user,
            notes=notes
        )
        
        # Send comprehensive order status notifications
        send_order_status_notifications(order, new_status, old_status)
        
        return Response({
            'message': f'Order status updated to {new_status}',
            'order': OrderSerializer(order, context={'request': request}).data
        })
        
    except (VendorProfile.DoesNotExist, Order.DoesNotExist):
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

# Review Views
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_review_api(request, order_id):
    """Create or update a review for a delivered order"""
    try:
        order = Order.objects.get(id=order_id, customer=request.user)
        
        # Check if order is delivered
        if order.status != 'delivered':
            return Response({
                'error': 'Order must be delivered to be reviewed'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if review already exists
        existing_review = getattr(order, 'review', None)
        
        if existing_review:
            # Update existing review
            serializer = OrderReviewSerializer(existing_review, data=request.data, partial=True)
            if serializer.is_valid():
                review = serializer.save()
                return Response({
                    'message': 'Review updated successfully',
                    'review': OrderReviewSerializer(review).data
                })
        else:
            # Create new review
            serializer = OrderReviewSerializer(data=request.data)
            if serializer.is_valid():
                review = serializer.save(order=order, customer=request.user)
                return Response({
                    'message': 'Review created successfully',
                    'review': OrderReviewSerializer(review).data
                }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

# Refund Views
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def request_refund_api(request, order_id):
    """Request a refund for an order"""
    try:
        order = Order.objects.get(id=order_id, customer=request.user)
        
        if order.status not in ['delivered', 'cancelled']:
            return Response({
                'error': 'Refund can only be requested for delivered or cancelled orders'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = OrderRefundSerializer(data=request.data)
        if serializer.is_valid():
            refund = serializer.save(order=order, customer=request.user)
            
            # Send refund notification
            send_refund_notification(refund, 'requested')
            
            return Response({
                'message': 'Refund request submitted successfully',
                'refund': OrderRefundSerializer(refund).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def request_return_api(request, order_id):
    """Request a return for a delivered order"""
    try:
        order = Order.objects.get(id=order_id, customer=request.user)
        
        if order.status != 'delivered':
            return Response({
                'error': 'Returns can only be requested for delivered orders'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if return already exists
        existing_return = OrderRefund.objects.filter(
            order=order, 
            status__in=['requested', 'approved', 'appeal']
        ).first()
        
        if existing_return:
            return Response({
                'error': 'Return request already exists for this order'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        data = request.data.copy()
        data['refund_type'] = 'full'
        
        serializer = OrderRefundSerializer(data=data)
        if serializer.is_valid():
            refund = serializer.save(order=order, customer=request.user)
            
            # Send refund notification
            send_refund_notification(refund, 'requested')
            
            return Response({
                'message': 'Return request submitted successfully',
                'refund': OrderRefundSerializer(refund).data
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def appeal_refund_api(request, refund_id):
    """Appeal a rejected refund request"""
    try:
        refund = OrderRefund.objects.get(id=refund_id, customer=request.user)
        
        if refund.status != 'rejected':
            return Response({
                'error': 'Can only appeal rejected refund requests'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update refund status to appeal
        refund.status = 'appeal'
        refund.appeal_at = timezone.now()
        refund.customer_notes = request.data.get('customer_notes', refund.customer_notes)
        refund.save()
        
        # Send refund notification for appeal
        send_refund_notification(refund, 'appeal')
        
        return Response({
            'message': 'Appeal submitted successfully',
            'refund': OrderRefundSerializer(refund).data
        })
        
    except OrderRefund.DoesNotExist:
        return Response({'error': 'Refund not found'}, status=status.HTTP_404_NOT_FOUND)

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
    """Process a refund request (admin or vendor)"""
    try:
        refund = OrderRefund.objects.get(id=refund_id)
        
        # Check if user has permission (admin or vendor of the order)
        has_permission = request.user.is_superuser
        if request.user.is_vendor:
            try:
                vendor_profile = VendorProfile.objects.get(user=request.user)
                has_permission = refund.order.vendor == vendor_profile
            except VendorProfile.DoesNotExist:
                has_permission = False
        
        if not has_permission:
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
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
    if not request.user.is_vendor:
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        vendor_profile = VendorProfile.objects.get(user=request.user)
        orders = Order.objects.filter(
            vendor=vendor_profile, 
            status='pending'
        ).order_by('-created_at')
        
        serializer = OrderSerializer(orders, many=True, context={'request': request})
        return Response(serializer.data)
        
    except VendorProfile.DoesNotExist:
        return Response({'error': 'Vendor profile not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def vendor_accept_order_api(request, order_id):
    """Accept an order (vendor only)"""
    if not request.user.is_vendor:
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        vendor_profile = VendorProfile.objects.get(user=request.user)
        order = Order.objects.get(id=order_id, vendor=vendor_profile, status='pending')
        
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
    if not request.user.is_vendor:
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
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
        if request.user.is_vendor:
            try:
                vendor_profile = VendorProfile.objects.get(user=request.user)
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
