# Production alternative - Database channel layer (slower but no Redis needed)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.DatabaseChannelLayer",
    }
}

# Or use Redis URL from environment
import os
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [REDIS_URL],
        },
    },
}