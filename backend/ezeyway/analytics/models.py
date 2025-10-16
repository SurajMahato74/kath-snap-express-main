from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()

class Visitor(models.Model):
    session_id = models.CharField(max_length=100, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    referrer = models.URLField(blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    device_type = models.CharField(max_length=50, blank=True, null=True)  # mobile, desktop, tablet
    browser = models.CharField(max_length=100, blank=True, null=True)
    os = models.CharField(max_length=100, blank=True, null=True)
    first_visit = models.DateTimeField(auto_now_add=True)
    last_visit = models.DateTimeField(auto_now=True)
    visit_count = models.IntegerField(default=1)
    is_known_user = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'analytics_visitor'
        
    def __str__(self):
        return f"{self.ip_address} - {self.session_id[:8]}"

class PageView(models.Model):
    visitor = models.ForeignKey(Visitor, on_delete=models.CASCADE, related_name='page_views')
    page_url = models.URLField()
    page_title = models.CharField(max_length=200, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    time_on_page = models.IntegerField(default=0)  # seconds
    exit_page = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'analytics_pageview'
        
    def __str__(self):
        return f"{self.visitor.ip_address} - {self.page_url}"

class Session(models.Model):
    visitor = models.ForeignKey(Visitor, on_delete=models.CASCADE, related_name='sessions')
    session_start = models.DateTimeField(auto_now_add=True)
    session_end = models.DateTimeField(null=True, blank=True)
    duration = models.IntegerField(default=0)  # seconds
    pages_visited = models.IntegerField(default=0)
    bounce = models.BooleanField(default=True)  # True if only 1 page visited
    
    class Meta:
        db_table = 'analytics_session'
        
    def __str__(self):
        return f"{self.visitor.ip_address} - {self.session_start}"

class TrafficSource(models.Model):
    SOURCE_CHOICES = [
        ('facebook', 'Facebook'),
        ('google', 'Google'),
        ('direct', 'Direct'),
        ('referral', 'Referral'),
        ('email', 'Email'),
        ('social', 'Social Media'),
        ('other', 'Other'),
    ]
    
    visitor = models.ForeignKey(Visitor, on_delete=models.CASCADE, related_name='traffic_sources')
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES)
    medium = models.CharField(max_length=100, blank=True, null=True)  # cpc, organic, etc
    campaign = models.CharField(max_length=200, blank=True, null=True)
    utm_source = models.CharField(max_length=100, blank=True, null=True)
    utm_medium = models.CharField(max_length=100, blank=True, null=True)
    utm_campaign = models.CharField(max_length=200, blank=True, null=True)
    utm_term = models.CharField(max_length=100, blank=True, null=True)
    utm_content = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_traffic_source'
        
    def __str__(self):
        return f"{self.visitor.ip_address} - {self.source}"