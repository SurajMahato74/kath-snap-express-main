from django.urls import path
from . import message_views
from . import fcm_test_views

urlpatterns = [
    # Conversation APIs
    path('conversations/', message_views.ConversationListView.as_view(), name='conversation_list'),
    path('conversations/create/', message_views.create_support_conversation_api, name='create_support_conversation'),
    path('conversations/<int:pk>/', message_views.ConversationDetailView.as_view(), name='conversation_detail'),
    path('conversations/<int:conversation_id>/messages/', message_views.MessageListView.as_view(), name='message_list'),
    path('conversations/user/<int:user_id>/', message_views.get_or_create_conversation_api, name='get_or_create_conversation'),
    
    # Message APIs
    path('messages/send/', message_views.send_message_api, name='send_message'),
    path('messages/<int:message_id>/read/', message_views.mark_message_read_api, name='mark_message_read'),
    path('messages/<int:message_id>/pin/', message_views.toggle_pin_message_api, name='toggle_pin_message'),
    path('messages/<int:message_id>/image/', message_views.message_image_api, name='message_image'),
    
    # Call APIs - ACTIVE
    path('create-call/', message_views.initiate_call_api, name='create_call'),
    path('calls/initiate/', message_views.initiate_call_api, name='initiate_call'),
    path('calls/<int:call_id>/answer/', message_views.answer_call_api, name='answer_call'),
    path('calls/<int:call_id>/end/', message_views.end_call_api, name='end_call'),
    path('calls/<int:call_id>/decline/', message_views.decline_call_api, name='decline_call'),
    path('calls/incoming/', message_views.incoming_calls_api, name='incoming_calls'),
    path('calls/history/', message_views.CallHistoryView.as_view(), name='call_history'),
    
    # FCM Test APIs
    path('test-fcm-call/', fcm_test_views.test_fcm_call_notification, name='test_fcm_call'),
    path('fcm-token/', fcm_test_views.get_fcm_token, name='get_fcm_token'),
    path('fcm-token/update/', fcm_test_views.update_fcm_token, name='update_fcm_token'),
]