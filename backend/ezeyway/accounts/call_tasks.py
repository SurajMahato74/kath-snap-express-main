from celery import shared_task
from django.utils import timezone
from django.db.models import Q
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging
import time

from .models import CustomUser
from .message_models import Call
from .models import VendorProfile
from .fcm_service import fcm_service

logger = logging.getLogger(__name__)

@shared_task
def cleanup_stale_calls():
    """
    Clean up calls that are stuck in 'initiated' or 'ringing' state for more than 5 minutes
    """
    cutoff_time = timezone.now() - timezone.timedelta(minutes=5)
    
    stale_calls = Call.objects.filter(
        status__in=['initiated', 'ringing'],
        initiated_at__lt=cutoff_time
    )
    
    for call in stale_calls:
        try:
            # Mark as missed
            call.status = 'missed'
            call.ended_at = timezone.now()
            call.save()
            
            # Send notifications
            send_missed_call_notifications.delay(call.id)
            
            # Clean up WebSocket room
            cleanup_call_websocket.delay(call.call_id)
            
            logger.info(f"Cleaned up stale call: {call.call_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up call {call.call_id}: {str(e)}")


@shared_task
def cleanup_ended_calls():
    """
    Clean up calls that have been ended but haven't been cleaned up for more than 1 hour
    """
    cutoff_time = timezone.now() - timezone.timedelta(hours=1)
    
    old_calls = Call.objects.filter(
        status__in=['ended', 'declined', 'missed'],
        ended_at__lt=cutoff_time
    )
    
    for call in old_calls:
        try:
            # Clean up WebSocket room
            cleanup_call_websocket.delay(call.call_id)
            
            logger.info(f"Cleaned up WebSocket room for ended call: {call.call_id}")
            
        except Exception as e:
            logger.error(f"Error cleaning up WebSocket for call {call.call_id}: {str(e)}")


@shared_task
def cleanup_orphaned_websockets():
    """
    Clean up WebSocket connections for calls that no longer exist
    """
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        
        # Get all active call groups
        from .routing import websocket_urlpatterns
        
        # This is a placeholder - in production, you might want to maintain
        # a separate registry of active call groups
        logger.info("Cleanup orphaned WebSockets task completed")
        
    except Exception as e:
        logger.error(f"Error cleaning up orphaned WebSockets: {str(e)}")


@shared_task
def send_missed_call_notifications(call_id):
    """
    Send FCM notifications for missed calls
    """
    try:
        call = Call.objects.get(id=call_id)
        
        # Notify caller that their call was missed
        if call.caller:
            try:
                vendor_profile = VendorProfile.objects.get(user=call.caller)
                if vendor_profile.fcm_token:
                    fcm_service.send_call_notification(
                        token=vendor_profile.fcm_token,
                        call_data={
                            'call_id': call.call_id,
                            'call_type': call.call_type,
                            'from_user': f"{call.callee.first_name} {call.callee.last_name}".strip() if call.callee else "Unknown",
                            'duration': 0,
                            'status': 'missed',
                            'action': 'call_missed'
                        }
                    )
            except VendorProfile.DoesNotExist:
                # Caller might be a customer, no FCM token
                pass
            except Exception as e:
                logger.error(f"Error sending missed call notification to caller: {str(e)}")
        
        # Notify callee about missed call
        if call.callee:
            try:
                vendor_profile = VendorProfile.objects.get(user=call.callee)
                if vendor_profile.fcm_token:
                    fcm_service.send_call_notification(
                        token=vendor_profile.fcm_token,
                        call_data={
                            'call_id': call.call_id,
                            'call_type': call.call_type,
                            'from_user': f"{call.caller.first_name} {call.caller.last_name}".strip(),
                            'status': 'missed',
                            'action': 'call_missed'
                        }
                    )
            except VendorProfile.DoesNotExist:
                # Callee might be a customer
                pass
            except Exception as e:
                logger.error(f"Error sending missed call notification to callee: {str(e)}")
        
        logger.info(f"Sent missed call notifications for call: {call.call_id}")
        
    except Call.DoesNotExist:
        logger.error(f"Call with id {call_id} not found")
    except Exception as e:
        logger.error(f"Error sending missed call notifications: {str(e)}")


@shared_task
def cleanup_call_websocket(call_id):
    """
    Clean up WebSocket group for a specific call
    """
    try:
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        
        call_group_name = f"call_{call_id}"
        
        # Send cleanup message to the group
        async_to_sync(channel_layer.group_send)(
            call_group_name,
            {
                'type': 'call_cleanup',
                'call_id': call_id,
                'message': 'Call session ended'
            }
        )
        
        logger.info(f"Sent cleanup message to WebSocket group: {call_group_name}")
        
    except Exception as e:
        logger.error(f"Error cleaning up WebSocket for call {call_id}: {str(e)}")


@shared_task
def send_call_quality_alerts(call_id, quality_data):
    """
    Send alerts for poor call quality
    """
    try:
        call = Call.objects.get(call_id=call_id)
        
        # Only send alerts for significant quality issues
        if quality_data.get('connection_quality') == 'poor':
            # Notify both participants about poor quality
            participants = [call.caller]
            if call.callee:
                participants.append(call.callee)
            
            for participant in participants:
                try:
                    vendor_profile = VendorProfile.objects.get(user=participant)
                    if vendor_profile.fcm_token:
                        fcm_service.send_call_notification(
                            token=vendor_profile.fcm_token,
                            call_data={
                                'call_id': call_id,
                                'call_type': call.call_type,
                                'status': 'poor_quality',
                                'action': 'quality_alert',
                                'quality_data': quality_data
                            }
                        )
                except VendorProfile.DoesNotExist:
                    continue
                except Exception as e:
                    logger.error(f"Error sending quality alert to user {participant.id}: {str(e)}")
        
        logger.info(f"Sent quality alerts for call: {call_id}")
        
    except Call.DoesNotExist:
        logger.error(f"Call with id {call_id} not found")
    except Exception as e:
        logger.error(f"Error sending quality alerts: {str(e)}")


@shared_task
def generate_call_analytics():
    """
    Generate call analytics and metrics (daily/hourly reports)
    """
    try:
        # This is a placeholder for analytics generation
        # You can expand this to generate detailed reports
        
        from datetime import timedelta
        
        # Get calls from last 24 hours
        yesterday = timezone.now() - timedelta(days=1)
        recent_calls = Call.objects.filter(initiated_at__gte=yesterday)
        
        # Calculate metrics
        total_calls = recent_calls.count()
        answered_calls = recent_calls.filter(status='answered').count()
        missed_calls = recent_calls.filter(status='missed').count()
        declined_calls = recent_calls.filter(status='declined').count()
        
        # Calculate average duration for answered calls
        answered_with_duration = recent_calls.filter(
            status='answered',
            duration__isnull=False
        )
        
        avg_duration = 0
        if answered_with_duration.exists():
            total_duration = sum(call.duration for call in answered_with_duration)
            avg_duration = total_duration / answered_with_duration.count()
        
        # Calculate success rate
        success_rate = 0
        if total_calls > 0:
            success_rate = (answered_calls / total_calls) * 100
        
        analytics_data = {
            'date': yesterday.date().isoformat(),
            'total_calls': total_calls,
            'answered_calls': answered_calls,
            'missed_calls': missed_calls,
            'declined_calls': declined_calls,
            'success_rate': round(success_rate, 2),
            'average_duration': round(avg_duration, 2),
            'total_duration': sum(call.duration or 0 for call in answered_with_duration)
        }
        
        # Store analytics (you might want to create an Analytics model)
        logger.info(f"Generated call analytics: {analytics_data}")
        
        # Send to monitoring system or store in database
        # analytics_store.delay(analytics_data)
        
    except Exception as e:
        logger.error(f"Error generating call analytics: {str(e)}")


@shared_task
def cleanup_call_history():
    """
    Clean up old call history (older than 30 days)
    """
    try:
        cutoff_date = timezone.now() - timezone.timedelta(days=30)
        
        # Archive old calls instead of deleting them
        old_calls = Call.objects.filter(
            initiated_at__lt=cutoff_date,
            status__in=['ended', 'declined', 'missed']
        )
        
        logger.info(f"Found {old_calls.count()} calls to archive")
        
        # Archive logic (move to another table or mark as archived)
        for call in old_calls:
            call.is_archived = True
            call.save()
        
        logger.info(f"Archived {old_calls.count()} old calls")
        
    except Exception as e:
        logger.error(f"Error cleaning up call history: {str(e)}")


@shared_task
def send_periodic_health_check():
    """
    Periodic health check for call system
    """
    try:
        # Check for stuck calls
        cutoff_time = timezone.now() - timezone.timedelta(minutes=10)
        stuck_calls = Call.objects.filter(
            status__in=['initiated', 'ringing'],
            initiated_at__lt=cutoff_time
        )
        
        if stuck_calls.exists():
            logger.warning(f"Found {stuck_calls.count()} stuck calls")
            # Trigger cleanup
            cleanup_stale_calls.delay()
        
        # Check WebSocket connections
        cleanup_orphaned_websockets.delay()
        
        logger.info("Call system health check completed")
        
    except Exception as e:
        logger.error(f"Error in periodic health check: {str(e)}")


@shared_task
def send_realtime_call_updates():
    """
    Send real-time updates about active calls to monitoring system
    """
    try:
        active_calls = Call.objects.filter(
            status__in=['initiated', 'ringing', 'answered']
        )
        
        for call in active_calls:
            # Send update to monitoring system
            channel_layer = get_channel_layer()
            if channel_layer:
                async_to_sync(channel_layer.group_send)(
                    f"call_monitoring",
                    {
                        'type': 'call_status_update',
                        'call_data': {
                            'call_id': call.call_id,
                            'status': call.status,
                            'initiated_at': call.initiated_at.isoformat(),
                            'duration': call.duration,
                            'call_type': call.call_type,
                            'participants': [
                                {'id': call.caller.id, 'name': call.caller.username},
                                {'id': call.callee.id, 'name': call.callee.username} if call.callee else None
                            ]
                        }
                    }
                )
        
        logger.info(f"Sent updates for {active_calls.count()} active calls")
        
    except Exception as e:
        logger.error(f"Error sending real-time call updates: {str(e)}")