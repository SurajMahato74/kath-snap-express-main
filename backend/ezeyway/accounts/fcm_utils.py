import json
import requests
import time
from django.conf import settings
from .models import FCMToken

def send_auto_open_fcm_message(user, order_id, order_number, amount):
    """
    Send high-priority data-only FCM message to auto-open the app
    """
    try:
        # Get user's FCM tokens
        fcm_tokens = FCMToken.objects.filter(user=user, is_active=True)
        
        if not fcm_tokens.exists():
            print(f"No FCM tokens found for user {user.id}")
            return False
        
        # Send multiple messages for reliability
        for fcm_token in fcm_tokens:
            # Message 1: Pure data message
            data_message = {
                "to": fcm_token.token,
                "priority": "high",
                "data": {
                    "autoOpen": "true",
                    "orderId": str(order_id),
                    "orderNumber": order_number,
                    "amount": amount,
                    "action": "autoOpenOrder",
                    "forceOpen": "true",
                    "timestamp": str(int(time.time())),
                    "type": "data_only"
                }
            }
            
            # Message 2: High priority with notification (for fallback)
            notification_message = {
                "to": fcm_token.token,
                "priority": "high",
                "notification": {
                    "title": "🔔 New Order!",
                    "body": f"Order #{order_number} - ₹{amount}",
                    "click_action": "FLUTTER_NOTIFICATION_CLICK",
                    "sound": "default"
                },
                "data": {
                    "autoOpen": "true",
                    "orderId": str(order_id),
                    "orderNumber": order_number,
                    "amount": amount,
                    "action": "autoOpenOrder",
                    "forceOpen": "true",
                    "type": "notification_with_data"
                },
                "android": {
                    "priority": "high",
                    "notification": {
                        "click_action": "FLUTTER_NOTIFICATION_CLICK",
                        "sound": "default"
                    }
                }
            }
            
            messages = [data_message, notification_message]
            
            # Send all messages
            headers = {
                'Authorization': f'key={settings.FCM_SERVER_KEY}',
                'Content-Type': 'application/json',
            }
            
            success_count = 0
            for i, message in enumerate(messages):
                try:
                    response = requests.post(
                        'https://fcm.googleapis.com/fcm/send',
                        headers=headers,
                        data=json.dumps(message)
                    )
                    
                    if response.status_code == 200:
                        print(f"✅ Auto-open FCM {i+1} sent successfully to {user.username}")
                        success_count += 1
                    else:
                        print(f"❌ Failed to send auto-open FCM {i+1}: {response.text}")
                        
                    # Small delay between messages
                    time.sleep(0.2)
                except Exception as e:
                    print(f"❌ Error sending message {i+1}: {e}")
            
            return success_count > 0
                
    except Exception as e:
        print(f"❌ Error sending auto-open FCM: {e}")
        return False
    
    return False

def send_background_trigger(user, order_data):
    """
    Send background trigger to force app opening
    """
    try:
        import time
        
        # Get user's FCM tokens
        fcm_tokens = FCMToken.objects.filter(user=user, is_active=True)
        
        for fcm_token in fcm_tokens:
            # Send multiple messages to ensure delivery
            for i in range(3):  # Send 3 times for reliability
                message = {
                    "to": fcm_token.token,
                    "priority": "high",
                    "data": {
                        "type": "background_trigger",
                        "autoOpen": "true",
                        "orderId": str(order_data.get('order_id', '')),
                        "orderNumber": order_data.get('order_number', ''),
                        "amount": str(order_data.get('amount', '')),
                        "timestamp": str(int(time.time())),
                        "attempt": str(i + 1)
                    }
                }
                
                headers = {
                    'Authorization': f'key={settings.FCM_SERVER_KEY}',
                    'Content-Type': 'application/json',
                }
                
                response = requests.post(
                    'https://fcm.googleapis.com/fcm/send',
                    headers=headers,
                    data=json.dumps(message)
                )
                
                print(f"Background trigger attempt {i+1}: {response.status_code}")
                time.sleep(0.5)  # Small delay between attempts
                
    except Exception as e:
        print(f"Error sending background trigger: {e}")