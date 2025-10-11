from django.utils import timezone
from .order_models import OrderNotification
from .consumers import send_vendor_notification, send_customer_notification

def create_order_notification(order, recipient, notification_type, title, message, send_realtime=True):
    """
    Create and send order notification to user
    """
    # Create database notification
    notification = OrderNotification.objects.create(
        order=order,
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message
    )
    
    # Send real-time notification if enabled
    if send_realtime:
        try:
            # Determine if recipient is vendor or customer
            if hasattr(recipient, 'vendor_profile'):
                # Send to vendor
                send_vendor_notification(
                    vendor_user_id=recipient.id,
                    notification_type='order',
                    title=title,
                    message=message,
                    data={
                        'order_id': order.id,
                        'order_number': order.order_number,
                        'notification_id': notification.id
                    },
                    action_url='/vendor/orders'
                )
            else:
                # Send to customer
                send_customer_notification(
                    customer_user_id=recipient.id,
                    notification_type='order',
                    title=title,
                    message=message,
                    data={
                        'order_id': order.id,
                        'order_number': order.order_number,
                        'notification_id': notification.id
                    },
                    action_url='/orders'
                )
        except Exception as e:
            print(f"Failed to send real-time notification: {e}")
    
    return notification

def send_order_status_notifications(order, new_status, old_status=None):
    """
    Send notifications for order status changes to both customer and vendor
    """
    # Define notification messages for each status
    customer_messages = {
        'pending': 'Your order has been placed successfully and is waiting for vendor confirmation.',
        'confirmed': 'Your order has been confirmed and is being prepared.',
        'preparing': 'Your order is being prepared by the vendor.',
        'ready_for_pickup': 'Your order is ready for pickup.',
        'out_for_delivery': 'Your order is out for delivery and will reach you soon.',
        'delivered': 'Your order has been delivered successfully. Enjoy your meal!',
        'cancelled': 'Your order has been cancelled.',
        'returned': 'Your order return has been processed.',
        'refunded': 'Your order refund has been processed.'
    }
    
    vendor_messages = {
        'pending': f'New order #{order.order_number} received from {order.customer.username}.',
        'confirmed': f'Order #{order.order_number} has been confirmed.',
        'preparing': f'Order #{order.order_number} is being prepared.',
        'ready_for_pickup': f'Order #{order.order_number} is ready for pickup.',
        'out_for_delivery': f'Order #{order.order_number} is out for delivery.',
        'delivered': f'Order #{order.order_number} has been delivered successfully.',
        'cancelled': f'Order #{order.order_number} has been cancelled.',
        'returned': f'Order #{order.order_number} return has been processed.',
        'refunded': f'Order #{order.order_number} refund has been processed.'
    }
    
    # Get notification titles
    titles = {
        'pending': 'Order Placed',
        'confirmed': 'Order Confirmed',
        'preparing': 'Order Being Prepared',
        'ready_for_pickup': 'Order Ready',
        'out_for_delivery': 'Out for Delivery',
        'delivered': 'Order Delivered',
        'cancelled': 'Order Cancelled',
        'returned': 'Order Returned',
        'refunded': 'Order Refunded'
    }
    
    # Send notification to customer
    if new_status in customer_messages:
        create_order_notification(
            order=order,
            recipient=order.customer,
            notification_type=f'order_{new_status}',
            title=titles.get(new_status, f'Order {new_status.title()}'),
            message=customer_messages[new_status],
            send_realtime=True
        )
    
    # Send notification to vendor (except for initial pending status)
    if new_status in vendor_messages and new_status != 'pending':
        create_order_notification(
            order=order,
            recipient=order.vendor.user,
            notification_type=f'order_{new_status}',
            title=titles.get(new_status, f'Order {new_status.title()}'),
            message=vendor_messages[new_status],
            send_realtime=True
        )
    
    # Special case: Send vendor notification for new orders (pending status) with AUTO-OPEN
    elif new_status == 'pending' and old_status is None:
        create_order_notification(
            order=order,
            recipient=order.vendor.user,
            notification_type='order_placed',
            title='New Order Received',
            message=vendor_messages['pending'],
            send_realtime=True
        )
        
        # Send FCM auto-open message
        print(f"NOTIFICATION_UTILS: Processing new order {order.id}")
        print(f"Vendor: {order.vendor.business_name}")
        print(f"Has FCM token: {hasattr(order.vendor, 'fcm_token')}")
        if hasattr(order.vendor, 'fcm_token'):
            print(f"FCM token exists: {bool(order.vendor.fcm_token)}")
            if order.vendor.fcm_token:
                print(f"FCM token: {order.vendor.fcm_token[:30]}...")
        
        try:
            if hasattr(order.vendor, 'fcm_token') and order.vendor.fcm_token:
                print(f"SENDING AUTO-OPEN FCM for order {order.id}")
                from .firebase_init import send_data_only_message
                
                try:
                    # Get order items safely
                    order_items = ", ".join([f"{item.quantity}x {item.product.name}" for item in order.orderitem_set.all()[:3]])
                    if order.orderitem_set.count() > 3:
                        order_items += "..."
                except:
                    order_items = "Order items"
                
                try:
                    customer_name = order.customer.get_full_name() or order.customer.username
                except:
                    customer_name = "Customer"
                
                fcm_data = {
                    "autoOpen": "true",
                    "orderId": str(order.id),
                    "orderNumber": order.order_number,
                    "customerName": customer_name,
                    "amount": str(order.total_amount),
                    "items": order_items,
                    "address": "Delivery address",
                    "action": "autoOpenOrder",
                    "forceOpen": "true"
                }
                
                notification_data = {
                    "title": f"🔥 NEW ORDER #{order.order_number}",
                    "body": f"{customer_name} • ${order.total_amount}"
                }
                print(f"FCM Data: {fcm_data}")
                
                from .firebase_init import send_fcm_message
                
                success = send_fcm_message(
                    token=order.vendor.fcm_token,
                    data=fcm_data,
                    notification=notification_data
                )
                
                if success:
                    print(f"SUCCESS: Auto-open FCM sent for order {order.id}")
                else:
                    print(f"FAILED: Auto-open FCM failed for order {order.id}")
            else:
                print(f"ERROR: No FCM token for vendor {order.vendor.business_name}")
        except Exception as e:
            print(f"EXCEPTION sending auto-open FCM: {e}")
            import traceback
            traceback.print_exc()

def send_payment_notification(order, payment_status):
    """
    Send payment status notifications
    """
    if payment_status == 'paid':
        # Notify vendor about payment received
        create_order_notification(
            order=order,
            recipient=order.vendor.user,
            notification_type='payment_received',
            title='Payment Received',
            message=f'Payment of ₹{order.total_amount} received for order #{order.order_number}.',
            send_realtime=True
        )
        
        # Notify customer about payment confirmation
        create_order_notification(
            order=order,
            recipient=order.customer,
            notification_type='payment_received',
            title='Payment Confirmed',
            message=f'Your payment of ₹{order.total_amount} for order #{order.order_number} has been confirmed.',
            send_realtime=True
        )
    
    elif payment_status == 'failed':
        # Notify customer about payment failure
        create_order_notification(
            order=order,
            recipient=order.customer,
            notification_type='payment_failed',
            title='Payment Failed',
            message=f'Payment for order #{order.order_number} has failed. Please try again.',
            send_realtime=True
        )

def send_refund_notification(refund, status_change):
    """
    Send refund status notifications
    """
    if status_change == 'requested':
        # Notify vendor about refund request
        create_order_notification(
            order=refund.order,
            recipient=refund.order.vendor.user,
            notification_type='refund_requested',
            title='Refund Request',
            message=f'Customer has requested refund for order #{refund.order.order_number}.',
            send_realtime=True
        )
        
        # Notify customer about refund request submission
        create_order_notification(
            order=refund.order,
            recipient=refund.customer,
            notification_type='refund_requested',
            title='Refund Request Submitted',
            message=f'Your refund request for order #{refund.order.order_number} has been submitted.',
            send_realtime=True
        )
    
    elif status_change == 'approved':
        # Notify customer about refund approval
        create_order_notification(
            order=refund.order,
            recipient=refund.customer,
            notification_type='refund_approved',
            title='Refund Approved',
            message=f'Your refund request for order #{refund.order.order_number} has been approved.',
            send_realtime=True
        )
    
    elif status_change == 'rejected':
        # Notify customer about refund rejection
        create_order_notification(
            order=refund.order,
            recipient=refund.customer,
            notification_type='refund_rejected',
            title='Refund Request Rejected',
            message=f'Your refund request for order #{refund.order.order_number} has been rejected. You can appeal this decision.',
            send_realtime=True
        )
    
    elif status_change == 'processed':
        # Notify customer about refund processing
        create_order_notification(
            order=refund.order,
            recipient=refund.customer,
            notification_type='refund_processed',
            title='Refund Processed',
            message=f'Your refund for order #{refund.order.order_number} has been processed and money has been transferred.',
            send_realtime=True
        )
    
    elif status_change == 'completed':
        # Notify customer about refund completion
        create_order_notification(
            order=refund.order,
            recipient=refund.customer,
            notification_type='refund_completed',
            title='Refund Completed',
            message=f'Your refund for order #{refund.order.order_number} has been completed successfully.',
            send_realtime=True
        )