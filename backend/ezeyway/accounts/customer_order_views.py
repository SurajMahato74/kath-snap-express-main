from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import permissions, status
from django.utils import timezone
from .order_models import Order, OrderStatusHistory, OrderRefund
from .order_serializers import OrderSerializer

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def customer_update_order_status_api(request, order_id):
    """Update order status (customer only - for marking as delivered)"""
    try:
        order = Order.objects.get(id=order_id, customer=request.user)
        
        new_status = request.data.get('status')
        notes = request.data.get('notes', '')
        
        if new_status != 'delivered' or order.status != 'out_for_delivery':
            return Response({'error': 'Invalid status update'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Update order status
        order.status = 'delivered'
        order.delivered_at = timezone.now()
        order.save()
        
        # Create status history
        OrderStatusHistory.objects.create(
            order=order,
            status='delivered',
            changed_by=request.user,
            notes=notes
        )
        
        return Response({
            'message': 'Order marked as delivered'
        })
        
    except Order.DoesNotExist:
        return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_refund_received_api(request, refund_id):
    """Mark refund as received by customer"""
    try:
        refund = OrderRefund.objects.get(id=refund_id, customer=request.user)
        
        if refund.status != 'completed':
            return Response({'error': 'Refund is not completed yet'}, status=status.HTTP_400_BAD_REQUEST)
        
        if refund.customer_received_refund:
            return Response({'error': 'Refund already marked as received'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Mark as received
        refund.customer_received_refund = True
        refund.customer_received_at = timezone.now()
        refund.save()
        
        return Response({
            'message': 'Refund marked as received successfully'
        })
        
    except OrderRefund.DoesNotExist:
        return Response({'error': 'Refund not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def contact_support_refund_api(request, refund_id):
    """Contact support for refund issues"""
    try:
        refund = OrderRefund.objects.get(id=refund_id, customer=request.user)
        
        if refund.status != 'completed':
            return Response({'error': 'Refund is not completed yet'}, status=status.HTTP_400_BAD_REQUEST)
        
        support_notes = request.data.get('notes', '')
        
        if not support_notes.strip():
            return Response({'error': 'Support notes are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Mark support contacted
        refund.support_contacted = True
        refund.support_contacted_at = timezone.now()
        refund.support_notes = support_notes
        refund.save()
        
        return Response({
            'message': 'Support contacted successfully. We will get back to you soon.'
        })
        
    except OrderRefund.DoesNotExist:
        return Response({'error': 'Refund not found'}, status=status.HTTP_404_NOT_FOUND)