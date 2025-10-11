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
            # Path to service account key
            service_account_path = 'c:/Users/suraj/OneDrive/Desktop/BRANDWAVE/ezeyway-2f869-firebase-adminsdk-fbsvc-d8638b05a4.json'
            
            if os.path.exists(service_account_path):
                cred = credentials.Certificate(service_account_path)
                firebase_admin.initialize_app(cred)
                logger.info("✅ Firebase Admin SDK initialized successfully")
            else:
                logger.warning("❌ Firebase service account file not found")
        except Exception as e:
            logger.error(f"❌ Firebase initialization failed: {e}")

    def send_order_notification(self, fcm_token, order_data):
        """Send FCM notification for new order"""
        try:
            if not fcm_token:
                logger.warning("No FCM token provided")
                return False

            # Create notification message
            message = messaging.Message(
                notification=messaging.Notification(
                    title='🔔 NEW ORDER RECEIVED',
                    body=f"Order #{order_data['orderNumber']} - ₹{order_data['amount']}"
                ),
                data={
                    'orderId': str(order_data['orderId']),
                    'orderNumber': order_data['orderNumber'],
                    'amount': str(order_data['amount']),
                    'action': 'openOrder',
                    'autoOpen': 'true'
                },
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        channel_id='order_alerts',
                        priority='high',
                        default_sound=True,
                        default_vibrate_timings=True,
                        default_light_settings=True
                    )
                ),
                token=fcm_token
            )

            # Send the message
            response = messaging.send(message)
            logger.info(f"✅ FCM notification sent successfully: {response}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send FCM notification: {e}")
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