import os
import sys

# Add project path
sys.path.insert(0, os.path.dirname(__file__))

# Set Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'ezeyway.settings'  # Replace 'ezeyway' with your project folder name

# Import WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
