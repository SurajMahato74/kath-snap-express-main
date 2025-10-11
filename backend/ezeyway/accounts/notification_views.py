from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from .order_models import OrderNotification
from .order_serializers import OrderNotificationSerializer

class NotificationListView(generics.ListAPIView):
    serializer_class = OrderNotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return OrderNotification.objects.filter(
            recipient=self.request.user
        ).order_by('-created_at')

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    try:
        notification = OrderNotification.objects.get(
            id=notification_id, 
            recipient=request.user
        )
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        
        return Response({'message': 'Notification marked as read'})
        
    except OrderNotification.DoesNotExist:
        return Response(
            {'error': 'Notification not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_all_notifications_read(request):
    """Mark all notifications as read for the current user"""
    notifications = OrderNotification.objects.filter(
        recipient=request.user,
        is_read=False
    )
    
    count = notifications.update(
        is_read=True,
        read_at=timezone.now()
    )
    
    return Response({
        'message': f'{count} notifications marked as read'
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def notification_count(request):
    """Get unread notification count"""
    unread_count = OrderNotification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()
    
    return Response({'unread_count': unread_count})

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def test_auto_open_notification(request):
    """Test auto-open FCM notification"""
    try:
        from .firebase_init import send_data_only_message
        from .models import VendorProfile
        
        # Get vendor's FCM token
        try:
            vendor_profile = VendorProfile.objects.get(user=request.user)
            fcm_token = vendor_profile.fcm_token
        except VendorProfile.DoesNotExist:
            return Response(
                {'error': 'Vendor profile not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not fcm_token:
            return Response(
                {'error': 'FCM token not found. Please restart the app.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Send auto-open FCM message
        success = send_data_only_message(
            token=fcm_token,
            data={
                "autoOpen": "true",
                "orderId": "999",
                "orderNumber": "TEST-AUTO-OPEN",
                "amount": "500",
                "action": "autoOpenOrder",
                "forceOpen": "true"
            }
        )
        
        return Response({
            'message': 'Auto-open test notification sent',
            'success': success,
            'user_id': request.user.id,
            'username': request.user.username
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to send test notification: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )