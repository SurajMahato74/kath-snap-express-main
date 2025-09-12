from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import permissions, status
from django.utils import timezone
from .order_models import Order, OrderStatusHistory
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