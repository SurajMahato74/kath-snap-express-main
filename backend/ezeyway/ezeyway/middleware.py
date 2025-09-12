class NgrokCorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Add ngrok-specific headers
        response['ngrok-skip-browser-warning'] = 'true'
        response['x-ngrok-skip-browser-warning'] = 'true'
        
        # Add Capacitor-specific headers
        if 'capacitor' in request.headers.get('user-agent', '').lower():
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, capacitor-platform, capacitor-version'
            response['Access-Control-Allow-Credentials'] = 'true'
        
        return response


class CapacitorMiddleware:
    """Middleware to handle Capacitor mobile app requests"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Handle preflight requests for Capacitor
        if request.method == 'OPTIONS':
            response = HttpResponse()
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, capacitor-platform, capacitor-version, ngrok-skip-browser-warning'
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Max-Age'] = '86400'
            return response
        
        response = self.get_response(request)
        
        # Add CORS headers for all responses
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Credentials'] = 'true'
        
        # Add Capacitor-specific headers
        if self.is_capacitor_request(request):
            response['capacitor-platform'] = request.headers.get('capacitor-platform', 'unknown')
            
        return response
    
    def is_capacitor_request(self, request):
        """Check if request is from Capacitor app"""
        user_agent = request.headers.get('user-agent', '').lower()
        return (
            'capacitor' in user_agent or
            request.headers.get('capacitor-platform') or
            request.headers.get('capacitor-version')
        )

from django.http import HttpResponse