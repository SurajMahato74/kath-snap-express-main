import os
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings

def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        # Check if Firebase is already initialized
        if firebase_admin._apps:
            print("Firebase already initialized")
            return True
            
        # Try to find service account file
        service_account_paths = [
            '/home/ezeywayc/kath-snap-express-main/ezeyway-2f869-firebase-adminsdk-fbsvc-d8638b05a4.json',
            '/home/ezeywayc/ezeyway-2f869-firebase-adminsdk-fbsvc-d8638b05a4.json',
            './ezeyway-2f869-firebase-adminsdk-fbsvc-d8638b05a4.json',
            os.path.join(settings.BASE_DIR.parent, 'ezeyway-2f869-firebase-adminsdk-fbsvc-d8638b05a4.json')
        ]
        
        service_account_file = None
        for path in service_account_paths:
            if os.path.exists(path):
                service_account_file = path
                print(f"Found service account file: {path}")
                break
        
        if not service_account_file:
            print("Firebase service account file not found")
            return False
            
        # Initialize Firebase
        cred = credentials.Certificate(service_account_file)
        firebase_admin.initialize_app(cred)
        
        print("Firebase Admin SDK initialized successfully")
        return True
        
    except Exception as e:
        print(f"Firebase initialization failed: {e}")
        return False

def send_fcm_message(token, title, body, data=None):
    """Send FCM message using Firebase Admin SDK"""
    try:
        if not firebase_admin._apps:
            if not initialize_firebase():
                return False
                
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            token=token,
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    click_action='FLUTTER_NOTIFICATION_CLICK',
                    sound='default'
                )
            )
        )
        
        response = messaging.send(message)
        print(f"FCM message sent successfully: {response}")
        return True
        
    except Exception as e:
        print(f"Failed to send FCM message: {e}")
        return False

def send_data_only_message(token, data):
    """Send FCM message with notification for auto-opening app"""
    try:
        if not firebase_admin._apps:
            if not initialize_firebase():
                return False
                
        message = messaging.Message(
            notification=messaging.Notification(
                title="New Order Received!",
                body=f"Order #{data.get('orderNumber', 'N/A')} - ₹{data.get('amount', '0')}"
            ),
            data=data,
            token=token,
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    sound='default',
                    click_action='FLUTTER_NOTIFICATION_CLICK',
                    channel_id='order_notifications'
                ),
                data=data
            )
        )
        
        response = messaging.send(message)
        print(f"Auto-open FCM message sent: {response}")
        return True
        
    except Exception as e:
        print(f"Failed to send auto-open FCM: {e}")
        return False
