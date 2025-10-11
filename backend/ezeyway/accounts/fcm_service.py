import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
import os
import logging

logger = logging.getLogger(__name__)

class FCMService:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FCMService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.initialize_firebase()
            self._initialized = True

    def initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if Firebase is already initialized
            if firebase_admin._apps:
                logger.info("✅ Firebase Admin SDK already initialized")
                return
            
            # Path to service account key
            service_account_path = os.environ.get('FIREBASE_SERVICE_ACCOUNT_PATH', 
                '/home/ezeywayc/kath-snap-express-main/ezeyway-2f869-firebase-adminsdk-fbsvc-d8638b05a4.json')
            
            # Alternative paths to try
            alternative_paths = [
                'c:/Users/suraj/OneDrive/Desktop/BRANDWAVE/kath-snap-express-main/ezeyway-2f869-firebase-adminsdk-fbsvc-d8638b05a4.json',
                '/home/ezeywayc/ezeyway-2f869-firebase-adminsdk-fbsvc-d8638b05a4.json',
                './ezeyway-2f869-firebase-adminsdk-fbsvc-d8638b05a4.json',
                '../ezeyway-2f869-firebase-adminsdk-fbsvc-d8638b05a4.json'
            ]
            
            # Try to find the service account file
            found_path = None
            if os.path.exists(service_account_path):
                found_path = service_account_path
            else:
                for path in alternative_paths:
                    if os.path.exists(path):
                        found_path = path
                        break
            
            if found_path:
                logger.info(f"📁 Using Firebase service account: {found_path}")
                cred = credentials.Certificate(found_path)
                firebase_admin.initialize_app(cred)
                logger.info("✅ Firebase Admin SDK initialized successfully")
            else:
                logger.error(f"❌ Firebase service account file not found. Tried paths: {[service_account_path] + alternative_paths}")
                
        except Exception as e:
            logger.error(f"❌ Firebase initialization failed: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def send_order_notification(self, fcm_token, order_data):
        """Send FCM data-only message to auto-open app for new order"""
        try:
            if not fcm_token:
                logger.warning("No FCM token provided")
                return False

            # Check if Firebase is initialized
            if not firebase_admin._apps:
                logger.error("❌ Firebase not initialized")
                return False

            logger.info(f"📤 Sending HIGH PRIORITY FCM notification to token: {fcm_token[:20]}...")
            logger.info(f"📊 Order data: {order_data}")
            logger.info("🚀 This will show notification that opens app when tapped!")

            # Send HIGH PRIORITY notification that FORCES app to open when tapped
            message = messaging.Message(
                notification=messaging.Notification(
                    title='🔔 NEW ORDER RECEIVED!',
                    body=f"Order #{order_data['orderNumber']} - ₹{order_data['amount']}\n🚀 TAP TO OPEN APP AUTOMATICALLY"
                ),
                data={
                    'orderId': str(order_data['orderId']),
                    'orderNumber': order_data['orderNumber'],
                    'amount': str(order_data['amount']),
                    'action': 'autoOpenOrder',
                    'autoOpen': 'true',
                    'forceOpen': 'true',
                    'type': 'order_notification'
                },
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        channel_id='order_alerts',
                        priority='max',
                        default_sound=True,
                        default_vibrate_timings=True,
                        default_light_settings=True,
                        sticky=True,
                        local_only=False,
                        notification_priority='PRIORITY_MAX',
                        visibility='public'
                    ),
                    data={
                        'orderId': str(order_data['orderId']),
                        'orderNumber': order_data['orderNumber'],
                        'amount': str(order_data['amount']),
                        'action': 'autoOpenOrder',
                        'autoOpen': 'true',
                        'forceOpen': 'true',
                        'type': 'order_notification'
                    }
                ),
                token=fcm_token
            )

            # Send the data-only message
            response = messaging.send(message)
            logger.info(f"✅ HIGH PRIORITY FCM notification sent successfully: {response}")
            logger.info("🚀 User will see notification and app will open when tapped!")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send FCM notification: {e}")
            import traceback
            logger.error(f"🔍 Full error traceback: {traceback.format_exc()}")
            return False

    def send_bulk_notification(self, fcm_tokens, title, body, data=None):
        """Send notification to multiple tokens"""
        try:
            if not fcm_tokens:
                logger.warning("No FCM tokens provided")
                return False

            # Create multicast message
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        channel_id='order_alerts',
                        priority='high',
                        default_sound=True
                    )
                ),
                tokens=fcm_tokens
            )

            # Send the message
            response = messaging.send_multicast(message)
            logger.info(f"✅ Bulk FCM notification sent: {response.success_count}/{len(fcm_tokens)} successful")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send bulk FCM notification: {e}")
            return False

# Global instance
fcm_service = FCMService()