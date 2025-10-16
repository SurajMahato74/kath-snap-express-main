from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone
from django.http import JsonResponse
from .models import Visitor, PageView, TrafficSource
from .utils import get_client_ip, parse_user_agent, get_location_from_ip, detect_traffic_source

@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def track_visit(request):
    """Track visitor from React frontend"""
    if request.method == 'GET':
        return JsonResponse({
            'message': 'Analytics tracking endpoint',
            'method': 'POST',
            'status': 'ready'
        })
    
    try:
        data = request.data
        
        # Get visitor info
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        referrer = data.get('referrer', '')
        page_url = data.get('page_url', '')
        page_title = data.get('page_title', '')
        session_id = data.get('session_id', '')
        
        # Location data from frontend
        country = data.get('country', '')
        city = data.get('city', '')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        # Create session key if not exists
        if not request.session.session_key:
            request.session.create()
        session_key = session_id or request.session.session_key
        
        # Get or create visitor
        visitor, created = Visitor.objects.get_or_create(
            session_id=session_key,
            defaults={
                'ip_address': ip_address,
                'user_agent': user_agent,
                'referrer': referrer,
                'country': country,
                'city': city,
            }
        )
        
        # Update visitor info
        if not created:
            visitor.visit_count += 1
            visitor.last_visit = timezone.now()
            
            # Update location if provided and not already set
            if country and not visitor.country:
                visitor.country = country
            if city and not visitor.city:
                visitor.city = city
                
            if request.user.is_authenticated and not visitor.user:
                visitor.user = request.user
                visitor.is_known_user = True
            visitor.save()
        else:
            # Parse user agent for new visitors
            ua_info = parse_user_agent(user_agent)
            
            visitor.device_type = ua_info.get('device_type')
            visitor.browser = ua_info.get('browser')
            visitor.os = ua_info.get('os')
            
            # Use frontend location data if available, otherwise try IP geolocation
            if not visitor.country and not country:
                location_info = get_location_from_ip(ip_address)
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
            page_url=page_url,
            page_title=page_title,
        )
        
        return Response({
            'status': 'success',
            'visitor_id': visitor.id,
            'is_new_visitor': created
        })
        
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=400)