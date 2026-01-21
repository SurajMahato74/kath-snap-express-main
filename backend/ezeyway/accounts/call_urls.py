from django.urls import path
from . import call_api_views

# Add these to your main urls.py
call_api_patterns = [
    # Frontend-compatible call APIs
    path('calls/create/', call_api_views.create_call_api, name='create_call_api'),
    path('fcm-token/update/', call_api_views.update_fcm_token_api, name='update_fcm_token_api'),
]