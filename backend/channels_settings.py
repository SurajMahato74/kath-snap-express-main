# Add these settings to your Django settings.py file

# Add 'channels' to INSTALLED_APPS
INSTALLED_APPS = [
    # ... your existing apps
    'channels',
]

# ASGI Configuration
ASGI_APPLICATION = 'ezeyway.asgi.application'

# Channel Layers Configuration (in-memory for development)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

# For production with Redis:
# CHANNEL_LAYERS = {
#     'default': {
#         'BACKEND': 'channels_redis.core.RedisChannelLayer',
#         'CONFIG': {
#             "hosts": [('127.0.0.1', 6379)],
#         },
#     },
# }