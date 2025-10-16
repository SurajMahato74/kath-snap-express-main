from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta
from .models import Visitor, PageView, Session, TrafficSource

@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = ['ip_address', 'session_display', 'country', 'city', 'device_type', 'browser_display', 'visit_count', 'is_known_user', 'first_visit', 'last_visit']
    list_filter = ['device_type', 'country', 'is_known_user', 'first_visit']
    search_fields = ['ip_address', 'session_id', 'user_agent', 'country', 'city']
    readonly_fields = ['session_id', 'ip_address', 'user_agent', 'first_visit', 'last_visit']
    date_hierarchy = 'first_visit'
    
    def session_display(self, obj):
        return obj.session_id[:12] + '...'
    session_display.short_description = 'Session ID'
    
    def browser_display(self, obj):
        return obj.browser[:30] + '...' if obj.browser and len(obj.browser) > 30 else obj.browser
    browser_display.short_description = 'Browser'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    list_display = ['visitor_ip', 'page_url_display', 'page_title', 'timestamp', 'time_on_page_display', 'exit_page']
    list_filter = ['timestamp', 'exit_page']
    search_fields = ['page_url', 'page_title', 'visitor__ip_address']
    readonly_fields = ['visitor', 'timestamp']
    date_hierarchy = 'timestamp'
    
    def visitor_ip(self, obj):
        return obj.visitor.ip_address
    visitor_ip.short_description = 'Visitor IP'
    
    def page_url_display(self, obj):
        return obj.page_url[:50] + '...' if len(obj.page_url) > 50 else obj.page_url
    page_url_display.short_description = 'Page URL'
    
    def time_on_page_display(self, obj):
        if obj.time_on_page:
            minutes = obj.time_on_page // 60
            seconds = obj.time_on_page % 60
            return f"{minutes}m {seconds}s"
        return "0s"
    time_on_page_display.short_description = 'Time on Page'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('visitor')

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ['visitor_ip', 'session_start', 'session_end', 'duration_display', 'pages_visited', 'bounce']
    list_filter = ['session_start', 'bounce']
    search_fields = ['visitor__ip_address']
    readonly_fields = ['visitor', 'session_start']
    date_hierarchy = 'session_start'
    
    def visitor_ip(self, obj):
        return obj.visitor.ip_address
    visitor_ip.short_description = 'Visitor IP'
    
    def duration_display(self, obj):
        if obj.duration:
            hours = obj.duration // 3600
            minutes = (obj.duration % 3600) // 60
            seconds = obj.duration % 60
            if hours:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"
        return "0s"
    duration_display.short_description = 'Duration'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('visitor')

@admin.register(TrafficSource)
class TrafficSourceAdmin(admin.ModelAdmin):
    list_display = ['visitor_ip', 'source', 'medium', 'campaign', 'utm_source', 'utm_campaign', 'created_at']
    list_filter = ['source', 'medium', 'created_at']
    search_fields = ['visitor__ip_address', 'utm_source', 'utm_campaign', 'campaign']
    readonly_fields = ['visitor', 'created_at']
    date_hierarchy = 'created_at'
    
    def visitor_ip(self, obj):
        return obj.visitor.ip_address
    visitor_ip.short_description = 'Visitor IP'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('visitor')

# Custom admin site for analytics dashboard
class AnalyticsAdminSite(admin.AdminSite):
    site_header = 'Website Analytics Dashboard'
    site_title = 'Analytics'
    index_title = 'Website Traffic Analytics'
    
    def index(self, request, extra_context=None):
        # Get analytics data for dashboard
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Today's stats
        today_visitors = Visitor.objects.filter(first_visit__date=today).count()
        today_pageviews = PageView.objects.filter(timestamp__date=today).count()
        
        # Yesterday's stats
        yesterday_visitors = Visitor.objects.filter(first_visit__date=yesterday).count()
        yesterday_pageviews = PageView.objects.filter(timestamp__date=yesterday).count()
        
        # Week stats
        week_visitors = Visitor.objects.filter(first_visit__date__gte=week_ago).count()
        week_pageviews = PageView.objects.filter(timestamp__date__gte=week_ago).count()
        
        # Month stats
        month_visitors = Visitor.objects.filter(first_visit__date__gte=month_ago).count()
        month_pageviews = PageView.objects.filter(timestamp__date__gte=month_ago).count()
        
        # Top traffic sources
        top_sources = TrafficSource.objects.values('source').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        # Top pages
        top_pages = PageView.objects.values('page_url').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Device breakdown
        device_stats = Visitor.objects.values('device_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        extra_context = extra_context or {}
        extra_context.update({
            'today_visitors': today_visitors,
            'today_pageviews': today_pageviews,
            'yesterday_visitors': yesterday_visitors,
            'yesterday_pageviews': yesterday_pageviews,
            'week_visitors': week_visitors,
            'week_pageviews': week_pageviews,
            'month_visitors': month_visitors,
            'month_pageviews': month_pageviews,
            'top_sources': top_sources,
            'top_pages': top_pages,
            'device_stats': device_stats,
        })
        
        return super().index(request, extra_context)