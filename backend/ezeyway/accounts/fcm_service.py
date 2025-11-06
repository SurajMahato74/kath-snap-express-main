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
        """Initialize Firebase Admin SDK with robust path detection"""
        try:
            # Check if Firebase is already initialized
            if firebase_admin._apps:
                logger.info("✅ Firebase Admin SDK already initialized")
                return

            # PRODUCTION-READY: More comprehensive path detection
            service_account_path = os.environ.get('FIREBASE_SERVICE_ACCOUNT_PATH')

            # If no environment variable, try multiple common locations
            if not service_account_path:
                # Get current working directory and try relative paths
                cwd = os.getcwd()
                base_paths = [
                    # Production server paths
                    '/home/ezeywayc/kath-snap-express-main/ezeyway-2f869-firebase-adminsdk-fbsvc-d8638b05a4.json',
                    '/var/www/html/ezeyway-2f869-firebase-adminsdk-fbsvc-d8638b05a4.json',
                    '/opt/ezeyway/ezeyway-2f869-firebase-adminsdk-fbsvc-d8638b05a4.json',
                    # Development paths
                    'c:/Users/suraj/OneDrive/Desktop/BRANDWAVE/kath-snap-express-main/ezeyway-2f869-firebase-adminsdk-fbsvc-d8638b05a4.json',
                    './ezeyway-2f869-firebase-adminsdk-fbsvc-d8638b05a4.json',
                    '../ezeyway-2f869-firebase-adminsdk-fbsvc-d8638b05a4.json',
                    '../../ezeyway-2f869-firebase-adminsdk-fbsvc-d8638b05a4.json',
                    # Relative to current working directory
                    os.path.join(cwd, 'ezeyway-2f869-firebase-adminsdk-fbsvc-d8638b05a4.json'),
                    os.path.join(cwd, '..', 'ezeyway-2f869-firebase-adminsdk-fbsvc-d8638b05a4.json'),
                    os.path.join(cwd, 'backend', 'ezeyway-2f869-firebase-adminsdk-fbsvc-d8638b05a4.json'),
                    os.path.join(cwd, '..', 'backend', 'ezeyway-2f869-firebase-adminsdk-fbsvc-d8638b05a4.json'),
                ]

                # Try to find the service account file
                found_path = None
                for path in base_paths:
                    if os.path.exists(path):
                        found_path = path
                        logger.info(f"📁 Found Firebase service account at: {path}")
                        break

                if not found_path:
                    # Last resort: search in common directories
                    logger.warning("🔍 Service account file not found in standard locations, searching...")
                    for root, dirs, files in os.walk('/home'):
                        if 'ezeyway-2f869-firebase-adminsdk-fbsvc-d8638b05a4.json' in files:
                            found_path = os.path.join(root, 'ezeyway-2f869-firebase-adminsdk-fbsvc-d8638b05a4.json')
                            logger.info(f"📁 Found Firebase service account via search: {found_path}")
                            break

                service_account_path = found_path

            if service_account_path and os.path.exists(service_account_path):
                logger.info(f"🔥 Using Firebase service account: {service_account_path}")
                cred = credentials.Certificate(service_account_path)
                firebase_admin.initialize_app(cred)
                logger.info("✅ Firebase Admin SDK initialized successfully")
            else:
                logger.error("❌ Firebase service account file not found!")
                logger.error("🔍 Searched in:")
                logger.error(f"   - Environment variable: {os.environ.get('FIREBASE_SERVICE_ACCOUNT_PATH', 'NOT SET')}")
                logger.error("   - Standard paths: /home/ezeywayc/, /var/www/, /opt/, current dir, parent dirs")
                logger.error("💡 Set FIREBASE_SERVICE_ACCOUNT_PATH environment variable to fix this")

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

    def send_web_push_notification(self, fcm_token, title, body, data=None, icon=None, badge=None):
        """Send web push notification that works when browser is closed"""
        try:
            if not fcm_token:
                logger.warning("No FCM token provided for web push")
                return False

            # Check if Firebase is initialized
            if not firebase_admin._apps:
                logger.error("❌ Firebase not initialized")
                return False

            logger.info(f"🌐 Sending WEB PUSH notification to token: {fcm_token[:20]}...")
            logger.info(f"📊 Web push data: title='{title}', body='{body}'")

            # Create web push message with high priority
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                webpush=messaging.WebpushConfig(
                    notification=messaging.WebpushNotification(
                        title=title,
                        body=body,
                        icon=icon or '/favicon.ico',
                        badge=badge or '/favicon.ico',
                        require_interaction=True,
                        silent=False,
                        tag='order-notification',
                        renotify=True
                    ),
                    fcm_options=messaging.WebpushFCMOptions(
                        link='https://yourdomain.com/vendor/orders'  # Replace with your actual domain
                    )
                ),
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        channel_id='order_alerts',
                        priority='max',
                        default_sound=True,
                        default_vibrate_timings=True,
                        sticky=True,
                        notification_priority='PRIORITY_MAX'
                    )
                ),
                token=fcm_token
            )

            # Send the web push message
            response = messaging.send(message)
            logger.info(f"✅ WEB PUSH notification sent successfully: {response}")
            logger.info("🌐 Notification will appear even when browser is closed!")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to send web push notification: {e}")
            import traceback
            logger.error(f"🔍 Full error traceback: {traceback.format_exc()}")
            return False

    def send_order_web_push_notification(self, fcm_token, order_data):
        """Send web push notification for new orders that works when browser closed"""
        try:
            title = f"🚨 New Order #{order_data['orderNumber']}"
            body = f"₹{order_data['amount']} - Tap to view order"

            data = {
                'orderId': str(order_data['orderId']),
                'orderNumber': order_data['orderNumber'],
                'amount': str(order_data['amount']),
                'action': 'openOrder',
                'type': 'order_notification',
                'timestamp': str(order_data.get('timestamp', ''))
            }

            return self.send_web_push_notification(
                fcm_token=fcm_token,
                title=title,
                body=body,
                data=data,
                icon='/alert-icon.svg',
                badge='/favicon.ico'
            )

        except Exception as e:
            logger.error(f"❌ Failed to send order web push notification: {e}")
            return False

# Global instance
fcm_service = FCMService()