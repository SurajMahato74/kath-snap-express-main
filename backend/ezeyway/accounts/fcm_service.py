import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
import os
import logging

logger = logging.getLogger(__name__)

# Import enums for correct priority/visibility
from firebase_admin.messaging import (
    AndroidNotificationPriority,
    AndroidNotificationVisibility,
)

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
        """Initialize Firebase Admin SDK with robust path detection"""
        try:
            if firebase_admin._apps:
                logger.info("Firebase Admin SDK already initialized")
                return

            service_account_path = os.environ.get('FIREBASE_SERVICEamp_ACCOUNT_PATH')

            if not service_account_path:
                cwd = os.getcwd()
                base_paths = [
                    '/opt/ezeyway/kath-snap-express-main/backend/ezeyway/ezeyway-2f869-firebase-adminsdk-fbsvc-debfce4d35.json',
                    '/opt/ezeyway/secrets/ezeyway-2f869-firebase-adminsdk-fbsvc-debfce4d35.json',
                    os.path.join(cwd, 'backend', 'ezeyway', 'ezeyway-2f869-firebase-adminsdk-fbsvc-debfce4d35.json'),
                    os.path.join(cwd, '..', 'backend', 'ezeyway', 'ezeyway-2f869-firebase-adminsdk-fbsvc-debfce4d35.json'),
                ]

                found_path = None
                for path in base_paths:
                    if os.path.exists(path):
                        found_path = path
                        logger.info(f"Found Firebase service account at: {path}")
                        break

                service_account_path = found_path

            if service_account_path and os.path.exists(service_account_path):
                logger.info(f"Using Firebase service account: {service_account_path}")
                cred = credentials.Certificate(service_account_path)
                firebase_admin.initialize_app(cred)
                logger.info("Firebase Admin SDK initialized successfully")
            else:
                logger.error("Firebase service account file not found!")
                logger.error(f"   - Env var: {os.environ.get('FIREBASE_SERVICE_ACCOUNT_PATH', 'NOT SET')}")
                logger.error("   - Standard paths: /opt/ezeyway/, current dir, parent dirs")
                logger.error("Set FIREBASE_SERVICE_ACCOUNT_PATH to fix this")

        except Exception as e:
            logger.error(f"Firebase initialization failed: {e}")
            import traceback
            logger.error(traceback.format_exc())

    def send_order_notification(self, fcm_token, order_data):
        """Send HIGH PRIORITY FCM notification that auto-opens app"""
        try:
            if not fcm_token:
                logger.warning("No FCM token provided")
                return False

            if not firebase_admin._apps:
                logger.error("Firebase not initialized")
                return False

            logger.info(f"Sending HIGH PRIORITY FCM to token: {fcm_token[:20]}...")
            logger.info(f"Order data: {order_data}")

            message = messaging.Message(
                token=fcm_token,
                notification=messaging.Notification(
                    title='NEW ORDER RECEIVED!',
                    body=f"Order #{order_data['orderNumber']} - ₹{order_data['amount']}\nTAP TO OPEN APP"
                ),
                data={
                    'orderId': str(order_data['orderId']),
                    'orderNumber': order_data['orderNumber'],
                    'amount': str(order_data['amount']),
                    'action': 'autoOpenOrder',
                    'autoOpen': 'true',
                    'forceOpen': 'true',
                    'type': 'order_notification',
                    'click_action': 'FLUTTER_NOTIFICATION_CLICK'
                },
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        channel_id='order_alerts',
                        priority=AndroidNotificationPriority.HIGH,
                        sound='default',
                        default_vibrate_timings=True,
                        default_light_settings=True,
                        sticky=True,
                        visibility=AndroidNotificationVisibility.PUBLIC,
                        click_action='FLUTTER_NOTIFICATION_CLICK'
                    )
                )
            )

            response = messaging.send(message)
            logger.info(f"FCM sent successfully: {response}")
            logger.info("Notification delivered – app will open on tap!")
            return True

        except Exception as e:
            logger.error(f"Failed to send FCM: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    def send_bulk_notification(self, fcm_tokens, title, body, data=None):
        """Send to multiple vendors"""
        try:
            if not fcm_tokens:
                logger.warning("No tokens for bulk send")
                return False

            message = messaging.MulticastMessage(
                notification=messaging.Notification(title=title, body=body),
                data=data or {},
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        channel_id='order_alerts',
                        priority=AndroidNotificationPriority.HIGH,
                        sound='default'
                    )
                ),
                tokens=fcm_tokens
            )

            response = messaging.send_multicast(message)
            logger.info(f"Bulk sent: {response.success_count}/{len(fcm_tokens)}")
            return response.success_count > 0

        except Exception as e:
            logger.error(f"Bulk FCM failed: {e}")
            return False

# Global singleton
fcm_service = FCMService()