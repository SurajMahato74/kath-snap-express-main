import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY
SECRET_KEY = 'django-insecure-g)8be^pfjk9cd+h!u)9$8(emxu7jj03mn$q7@7=^0t=(t=w81&'
DEBUG = True  # Set to False in production
ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'ezeyway.com', 'www.ezeyway.com','4046dc4ff1d1.ngrok-free.app','YOUR_NEW_NGROK_URL.ngrok-free.app',]  # Replace YOUR_NEW_NGROK_URL with actual ngrok URL

# Installed apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'accounts',
    'channels',
]
ASGI_APPLICATION = 'ezeyway.asgi.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}
# Middleware
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'ezeyway.middleware.CapacitorMiddleware',
    'ezeyway.middleware.NgrokCorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',  # Disabled for API development
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ezeyway.urls'

# Database (MySQL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'ezeyway',       # MySQL database name
        'USER': 'root',       # MySQL username
        'PASSWORD': 'root',   # MySQL password
        'HOST': 'localhost',          # Usually localhost in cPanel
        'PORT': '3306',               # Default MySQL port
    }
}

WSGI_APPLICATION = 'ezeyway.wsgi.application'

# Static files (CSS, JS)
STATIC_URL = '/assets/'
STATICFILES_DIRS = [
    BASE_DIR / "dist" / "assets",
]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Media files (User uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / "media"

# Use ngrok URL for media files when running through ngrok
if '150e57c57d60.ngrok-free.app' in str(ALLOWED_HOSTS):
    MEDIA_URL = 'https://4046dc4ff1d1.ngrok-free.app/media/'

# React build files
REACT_URL = '/'
REACT_ROOT = BASE_DIR / "dist"

# Templates (React index.html)
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "dist"],  # React index.html
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'accounts.CustomUser'

# Authentication Backends
AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailOrUsernameBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'm.suraj1123@gmail.com'  # Replace with your email
EMAIL_HOST_PASSWORD = 'eimg hdsw rjvr nzba'  # Replace with your app password
DEFAULT_FROM_EMAIL = 'EzeyWay <m.suraj1123@gmail.com>'

# OTP Settings
OTP_EXPIRY_MINUTES = 10
VERIFICATION_TOKEN_EXPIRY_HOURS = 24
PASSWORD_RESET_TOKEN_EXPIRY_HOURS = 2

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20
}

# CORS Settings - Optimized for ngrok and mobile
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding', 
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'ngrok-skip-browser-warning',
    'x-ngrok-skip-browser-warning',
    'capacitor-platform',
    'capacitor-version',
]
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET', 
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
CORS_PREFLIGHT_MAX_AGE = 86400
CORS_EXPOSE_HEADERS = [
    'Content-Type',
    'X-CSRFToken',
    'ngrok-skip-browser-warning',
    'x-ngrok-skip-browser-warning',
]

# Ngrok-specific settings
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# CSRF Settings
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8080',
    'http://127.0.0.1:8080',
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'https://150e57c57d60.ngrok-free.app',
    'https://4046dc4ff1d1.ngrok-free.app',
    'capacitor://localhost',
    'ionic://localhost',
    'http://localhost',
    'https://localhost',
    'https://localhost:8080',
    'https://localhost:3000',
]

# Additional settings for mobile app
ALLOWED_HOSTS.extend([
    '192.168.1.1',  # Add your local IP
    '10.0.2.2',     # Android emulator
    '127.0.0.1',
    'localhost'
])
