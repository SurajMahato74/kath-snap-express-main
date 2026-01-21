"""
Call Status API
Provides endpoints for call state checking and synchronization
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .message_models import Call
from .call_state_manager import call_state_manager
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_call_status_api(request, call_id):
    """Get current call status"""
    try:
        call = Call.objects.get(call_id=call_id)
        
        # Check if user has access
        if call.caller != request.user and call.receiver != request.user:
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        return Response({
            'call_id': call_id,
            'status': call.status,
            'started_at': call.started_at.isoformat() if call.started_at else None,
            'answered_at': call.answered_at.isoformat() if call.answered_at else None,
            'ended_at': call.ended_at.isoformat() if call.ended_at else None,
            'duration': call.duration or 0,
            'caller_id': call.caller.id,
            'receiver_id': call.receiver.id if call.receiver else None
        })
        
    except Call.DoesNotExist:
        return Response({'error': 'Call not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_call_status_api(request, call_id):
    """Sync call status across participants"""
    try:
        new_status = request.data.get('status')
        if not new_status:
            return Response({'error': 'Status required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate status values
        valid_statuses = ['initiated', 'ringing', 'answered', 'active', 'ended', 'declined', 'missed']
        if new_status not in valid_statuses:
            return Response({
                'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Sync state
        call_state_manager.sync_call_state(call_id, request.user.id, new_status)
        
        return Response({
            'success': True,
            'call_id': call_id,
            'status': new_status,
            'synced_at': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Call status sync error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reconnect_call_api(request, call_id):
    """Handle call reconnection"""
    try:
        call_state_manager.handle_reconnect(call_id, request.user.id)
        
        return Response({
            'success': True,
            'call_id': call_id,
            'reconnected_at': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Call reconnect error: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)