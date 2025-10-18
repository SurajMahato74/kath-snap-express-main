#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime, timedelta

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ezeyway.settings')
django.setup()

from django.utils import timezone
from analytics.models import Visitor, PageView

def debug_dates():
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    print(f"Today: {today}")
    print(f"Week ago: {week_ago}")
    print(f"Month ago: {month_ago}")
    
    # Check visitor dates
    visitors = Visitor.objects.all()
    print(f"\nTotal visitors: {visitors.count()}")
    
    for v in visitors:
        visit_date = v.first_visit.date()
        print(f"Visitor {v.ip_address}: {visit_date}")
        print(f"  - Is within week? {visit_date >= week_ago}")
        print(f"  - Is within month? {visit_date >= month_ago}")
    
    # Test the actual queries
    week_visitors = Visitor.objects.filter(first_visit__date__gte=week_ago).count()
    month_visitors = Visitor.objects.filter(first_visit__date__gte=month_ago).count()
    
    print(f"\nWeek visitors query result: {week_visitors}")
    print(f"Month visitors query result: {month_visitors}")

if __name__ == '__main__':
    debug_dates()