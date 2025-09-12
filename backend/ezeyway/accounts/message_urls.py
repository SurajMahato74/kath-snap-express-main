from django.urls import path
from . import message_views

urlpatterns = [
    # Conversation APIs
    path('conversations/', message_views.ConversationListView.as_view(), name='conversation_list'),
    path('conversations/<int:pk>/', message_views.ConversationDetailView.as_view(), name='conversation_detail'),
    path('conversations/<int:conversation_id>/messages/', message_views.MessageListView.as_view(), name='message_list'),
    path('conversations/user/<int:user_id>/', message_views.get_or_create_conversation_api, name='get_or_create_conversation'),
    
    # Message APIs
    path('messages/send/', message_views.send_message_api, name='send_message'),
    path('messages/<int:message_id>/read/', message_views.mark_message_read_api, name='mark_message_read'),
    path('messages/<int:message_id>/pin/', message_views.toggle_pin_message_api, name='toggle_pin_message'),
    
    # Call APIs
    path('calls/initiate/', message_views.initiate_call_api, name='initiate_call'),
    path('calls/<int:call_id>/answer/', message_views.answer_call_api, name='answer_call'),
    path('calls/<int:call_id>/end/', message_views.end_call_api, name='end_call'),
    path('calls/<int:call_id>/decline/', message_views.decline_call_api, name='decline_call'),
    path('calls/incoming/', message_views.incoming_calls_api, name='incoming_calls'),
    path('calls/history/', message_views.CallHistoryView.as_view(), name='call_history'),
]