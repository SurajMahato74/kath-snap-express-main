#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ezeyway.settings')
django.setup()

from analytics.models import Visitor, PageView, TrafficSource
from django.utils import timezone
from datetime import timedelta

def check_analytics_data():
    print("=== Analytics Data Check ===\n")
    
    # Check visitors
    visitors = Visitor.objects.all().order_by('-first_visit')
    print(f"Total Visitors: {visitors.count()}")
    
    if visitors.exists():
        print("\nRecent Visitors:")
        for v in visitors[:5]:
            print(f"  IP: {v.ip_address}, First Visit: {v.first_visit}, Visits: {v.visit_count}")
    
    # Check page views
    pageviews = PageView.objects.all().order_by('-timestamp')
    print(f"\nTotal Page Views: {pageviews.count()}")
    
    if pageviews.exists():
        print("\nRecent Page Views:")
        for pv in pageviews[:5]:
            print(f"  URL: {pv.page_url}, Time: {pv.timestamp}")
    
    # Check traffic sources
    sources = TrafficSource.objects.all()
    print(f"\nTotal Traffic Sources: {sources.count()}")
    
    if sources.exists():
        print("\nTraffic Sources:")
        for ts in sources:
            print(f"  Source: {ts.source}, Visitor: {ts.visitor.ip_address}")
    
    # Check date ranges
    today = timezone.now().date()
    print(f"\nToday's Date: {today}")
    
    today_visitors = Visitor.objects.filter(first_visit__date=today).count()
    today_pageviews = PageView.objects.filter(timestamp__date=today).count()
    
    print(f"Today's Visitors: {today_visitors}")
    print(f"Today's Page Views: {today_pageviews}")
    
    # Check last 7 days
    week_ago = today - timedelta(days=7)
    week_visitors = Visitor.objects.filter(first_visit__date__gte=week_ago).count()
    week_pageviews = PageView.objects.filter(timestamp__date__gte=week_ago).count()
    
    print(f"Last 7 Days Visitors: {week_visitors}")
    print(f"Last 7 Days Page Views: {week_pageviews}")
    
    # Show all visitor dates
    print("\nAll Visitor Dates:")
    for v in visitors:
        print(f"  {v.ip_address}: {v.first_visit.date()}")

if __name__ == '__main__':
    check_analytics_data()