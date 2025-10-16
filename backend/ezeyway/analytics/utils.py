import re
from urllib.parse import urlparse, parse_qs

def get_client_ip(request):
    """Get the real IP address of the client"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def parse_user_agent(user_agent_string):
    """Simple user agent parsing without external dependencies"""
    try:
        ua = user_agent_string.lower()
        
        # Determine device type
        if 'mobile' in ua or 'android' in ua or 'iphone' in ua:
            device_type = 'mobile'
        elif 'tablet' in ua or 'ipad' in ua:
            device_type = 'tablet'
        else:
            device_type = 'desktop'
            
        # Determine browser
        if 'chrome' in ua:
            browser = 'Chrome'
        elif 'firefox' in ua:
            browser = 'Firefox'
        elif 'safari' in ua:
            browser = 'Safari'
        elif 'edge' in ua:
            browser = 'Edge'
        else:
            browser = 'Unknown'
            
        # Determine OS
        if 'windows' in ua:
            os = 'Windows'
        elif 'mac' in ua:
            os = 'macOS'
        elif 'linux' in ua:
            os = 'Linux'
        elif 'android' in ua:
            os = 'Android'
        elif 'ios' in ua:
            os = 'iOS'
        else:
            os = 'Unknown'
            
        return {
            'device_type': device_type,
            'browser': browser,
            'os': os,
        }
    except:
        return {
            'device_type': 'unknown',
            'browser': 'unknown',
            'os': 'unknown',
        }

def get_location_from_ip(ip_address):
    """Simple location detection for localhost"""
    if ip_address in ['127.0.0.1', 'localhost', '::1']:
        return {'country': 'Local', 'city': 'Local'}
    return {'country': 'Unknown', 'city': 'Unknown'}

def detect_traffic_source(request):
    """Detect traffic source from referrer and UTM parameters"""
    referrer = request.META.get('HTTP_REFERER', '')
    
    # Get UTM parameters
    utm_source = request.GET.get('utm_source', '')
    utm_medium = request.GET.get('utm_medium', '')
    utm_campaign = request.GET.get('utm_campaign', '')
    utm_term = request.GET.get('utm_term', '')
    utm_content = request.GET.get('utm_content', '')
    
    # Determine source
    source = 'direct'
    medium = ''
    campaign = ''
    
    if utm_source:
        source = utm_source.lower()
        medium = utm_medium
        campaign = utm_campaign
    elif referrer:
        parsed_referrer = urlparse(referrer)
        domain = parsed_referrer.netloc.lower()
        
        if 'facebook.com' in domain or 'fb.com' in domain:
            source = 'facebook'
            medium = 'referral'
        elif 'google.com' in domain:
            source = 'google'
            medium = 'organic'
        elif 'instagram.com' in domain:
            source = 'instagram'
            medium = 'social'
        elif 'twitter.com' in domain or 'x.com' in domain:
            source = 'twitter'
            medium = 'social'
        else:
            source = 'referral'
            medium = 'referral'
    
    return {
        'source': source,
        'medium': medium,
        'campaign': campaign,
        'utm_source': utm_source,
        'utm_medium': utm_medium,
        'utm_campaign': utm_campaign,
        'utm_term': utm_term,
        'utm_content': utm_content,
    }