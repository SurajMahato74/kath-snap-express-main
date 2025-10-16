from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from django.http import JsonResponse
from .models import Visitor, PageView, TrafficSource

def analytics_test(request):
    """Simple test page to verify analytics is working"""
    visitors_count = Visitor.objects.count()
    pageviews_count = PageView.objects.count()
    
    return JsonResponse({
        'status': 'Analytics working!',
        'total_visitors': visitors_count,
        'total_pageviews': pageviews_count,
        'test_url': 'http://localhost:8000/api/analytics/track/',
        'admin_url': 'http://localhost:8000/api/admin/',
    })

# Analytics dashboard moved to accounts app