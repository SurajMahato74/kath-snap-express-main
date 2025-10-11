from django.urls import path
from . import notification_views

urlpatterns = [
    path('', notification_views.NotificationListView.as_view(), name='api_notifications'),
    path('<int:notification_id>/read/', notification_views.mark_notification_read, name='api_mark_notification_read'),
    path('mark-all-read/', notification_views.mark_all_notifications_read, name='api_mark_all_notifications_read'),
    path('count/', notification_views.notification_count, name='api_notification_count'),
    path('test-auto-open/', notification_views.test_auto_open_notification, name='api_test_auto_open'),
]