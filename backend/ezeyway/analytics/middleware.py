import re
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from django.contrib.sessions.models import Session as DjangoSession
from .models import Visitor, PageView, Session, TrafficSource
from .utils import get_client_ip, parse_user_agent, get_location_from_ip, detect_traffic_source

class AnalyticsMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Skip for admin, API, and static files
        if any(request.path.startswith(path) for path in ['/admin/', '/api/', '/static/', '/media/']):
            return None
            
        # Get visitor info
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        referrer = request.META.get('HTTP_REFERER', '')
        session_key = request.session.session_key
        
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
            
        # Get or create visitor
        visitor, created = Visitor.objects.get_or_create(
            session_id=session_key,
            defaults={
                'ip_address': ip_address,
                'user_agent': user_agent,
                'referrer': referrer,
            }
        )
        
        # Update visitor info if not created
        if not created:
            visitor.visit_count += 1
            visitor.last_visit = timezone.now()
            if request.user.is_authenticated and not visitor.user:
                visitor.user = request.user
                visitor.is_known_user = True
            visitor.save()
        else:
            # Parse user agent for new visitors
            ua_info = parse_user_agent(user_agent)
            location_info = get_location_from_ip(ip_address)
            
            visitor.device_type = ua_info.get('device_type')
            visitor.browser = ua_info.get('browser')
            visitor.os = ua_info.get('os')
            visitor.country = location_info.get('country')
            visitor.city = location_info.get('city')
            
            if request.user.is_authenticated:
                visitor.user = request.user
                visitor.is_known_user = True
                
            visitor.save()
            
            # Track traffic source for new visitors
            source_info = detect_traffic_source(request)
            if source_info:
                TrafficSource.objects.create(
                    visitor=visitor,
                    **source_info
                )
        
        # Create page view
        PageView.objects.create(
            visitor=visitor,
            page_url=request.build_absolute_uri(),
            page_title=request.GET.get('title', ''),
        )
        
        # Store visitor in request for later use
        request.visitor = visitor
        
        return None