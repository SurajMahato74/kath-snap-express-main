from django.urls import path
from . import api_views

urlpatterns = [
    path('track/', api_views.track_visit, name='track_visit'),
]