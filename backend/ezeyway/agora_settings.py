# Add these to your Django settings.py

import os

# Agora Configuration - Use environment variables in production
AGORA_APP_ID = os.getenv('AGORA_APP_ID', '51aafec601fa444581210f9fac99a73a')
AGORA_APP_CERTIFICATE = os.getenv('AGORA_APP_CERTIFICATE', '0c85813471a1416cadab8a3d77d4fc7f')

# WebRTC Configuration
WEBRTC_SETTINGS = {
    'STUN_SERVERS': [
        'stun:stun.l.google.com:19302',
        'stun:stun1.l.google.com:19302',
    ],
    'TURN_SERVERS': [
        # Add TURN servers if needed for NAT traversal
    ]
}

# Call Configuration
CALL_SETTINGS = {
    'MAX_CALL_DURATION': 3600,  # 1 hour in seconds
    'TOKEN_EXPIRY': 7200,       # 2 hours in seconds
    'RECONNECT_TIMEOUT': 30,    # Seconds to wait for reconnection
    'STATE_SYNC_INTERVAL': 5,   # Seconds between state sync
    'ENABLE_RECORDING': False,
    'ENABLE_TRANSCRIPTION': False
}