#!/usr/bin/env python
"""
WebSocket Call Notification Test Script

This script tests the complete call notification flow:
1. Connect to WebSocket as receiver
2. Initiate call via API
3. Verify WebSocket receives incoming_call notification
4. Answer the call
5. End the call

Usage: python test_websocket_call_notifications.py
"""

import asyncio
import json
import logging
import os
import sys
import time
import websockets
import requests
from datetime import datetime

# Setup Django environment
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ezeyway.settings')

import django
django.setup()

from django.contrib.auth import get_user_model
from accounts.message_models import Call

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WebSocketCallTester:
    def __init__(self):
        self.base_url = "https://ezeyway.com"  # Production URL
        self.ws_url = "wss://ezeyway.com"  # Production WebSocket URL
        self.received_notifications = []
        self.websocket_task = None

    async def websocket_listener(self, user_token):
        """Listen for WebSocket notifications"""
        try:
            uri = f"{self.ws_url}/ws/messages/?token={user_token}"
            logger.info(f"🔌 Connecting to WebSocket: {uri}")

            async with websockets.connect(uri) as websocket:
                logger.info("✅ WebSocket connected")

                while True:
                    try:
                        message = await websocket.recv()
                        data = json.loads(message)
                        logger.info(f"📬 Received: {data}")

                        self.received_notifications.append({
                            'timestamp': datetime.now().isoformat(),
                            'data': data
                        })

                        # Handle incoming call
                        if data.get('type') == 'incoming_call':
                            logger.info("📞 Incoming call notification received!")
                            return data.get('call', {})

                    except websockets.exceptions.ConnectionClosed:
                        logger.info("🔌 WebSocket connection closed")
                        break
                    except Exception as e:
                        logger.error(f"❌ WebSocket error: {e}")
                        break

        except Exception as e:
            logger.error(f"❌ WebSocket connection failed: {e}")
            return None

    def get_user_token(self, user_id):
        """Get authentication token for user (for local testing)"""
        try:
            from rest_framework.authtoken.models import Token
            user = get_user_model().objects.get(id=user_id)
            token, created = Token.objects.get_or_create(user=user)
            return token.key
        except Exception as e:
            logger.error(f"❌ Failed to get token for user {user_id}: {e}")
            return None

    def initiate_call_api(self, caller_token, recipient_id):
        """Initiate call via API"""
        try:
            headers = {
                'Authorization': f'Token {caller_token}',
                'Content-Type': 'application/json'
            }

            data = {
                'recipient_id': recipient_id,
                'call_type': 'audio'
            }

            response = requests.post(
                f"{self.base_url}/api/accounts/initiate-call/",
                headers=headers,
                json=data
            )

            logger.info(f"📞 Call initiation response: {response.status_code}")
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ Call initiated: {result}")
                return result
            else:
                logger.error(f"❌ Call initiation failed: {response.text}")
                return None

        except Exception as e:
            logger.error(f"❌ API call failed: {e}")
            return None

    def answer_call_api(self, user_token, call_id):
        """Answer call via API"""
        try:
            headers = {
                'Authorization': f'Token {user_token}',
                'Content-Type': 'application/json'
            }

            response = requests.post(
                f"{self.base_url}/api/accounts/answer-call/",
                headers=headers,
                json={'call_id': call_id}
            )

            logger.info(f"📞 Answer call response: {response.status_code}")
            return response.status_code == 200

        except Exception as e:
            logger.error(f"❌ Answer call failed: {e}")
            return False

    def end_call_api(self, user_token, call_id):
        """End call via API"""
        try:
            headers = {
                'Authorization': f'Token {user_token}',
                'Content-Type': 'application/json'
            }

            response = requests.post(
                f"{self.base_url}/api/accounts/end-call/",
                headers=headers,
                json={'call_id': call_id}
            )

            logger.info(f"📞 End call response: {response.status_code}")
            return response.status_code == 200

        except Exception as e:
            logger.error(f"❌ End call failed: {e}")
            return False

    async def test_call_flow(self, caller_token=None, receiver_token=None, receiver_id=None):
        """Test complete call flow with WebSocket notifications"""
        logger.info("🚀 Starting WebSocket Call Notification Test")

        # For production testing, use provided tokens
        if caller_token and receiver_token and receiver_id:
            logger.info("🔑 Using provided tokens for production testing")
        else:
            # Local testing - get tokens from database
            caller_id = 1  # Adjust to actual user ID
            receiver_id = 2  # Adjust to actual user ID

            caller_token = self.get_user_token(caller_id)
            receiver_token = self.get_user_token(receiver_id)

            if not caller_token or not receiver_token:
                logger.error("❌ Failed to get user tokens")
                return False

        logger.info(f"👤 Receiver ID: {receiver_id}, Token: {receiver_token[:10]}...")
        logger.info(f"👤 Caller Token: {caller_token[:10]}...")

        # Start WebSocket listener for receiver
        logger.info("🔄 Starting WebSocket listener for receiver...")
        websocket_future = asyncio.create_task(self.websocket_listener(receiver_token))

        # Wait a moment for WebSocket to connect
        await asyncio.sleep(2)

        # Initiate call
        logger.info("📞 Initiating call...")
        call_result = self.initiate_call_api(caller_token, receiver_id)

        if not call_result:
            logger.error("❌ Call initiation failed")
            websocket_future.cancel()
            return False

        call_id = call_result.get('call_id')
        logger.info(f"✅ Call initiated with ID: {call_id}")

        # Wait for WebSocket notification
        logger.info("⏳ Waiting for incoming call notification...")
        try:
            call_data = await asyncio.wait_for(websocket_future, timeout=10.0)
        except asyncio.TimeoutError:
            logger.error("❌ Timeout waiting for WebSocket notification")
            websocket_future.cancel()
            return False

        if not call_data:
            logger.error("❌ No call data received via WebSocket")
            return False

        logger.info(f"✅ Received call notification: {call_data}")

        # Verify call data
        if call_data.get('call_id') != call_id:
            logger.error(f"❌ Call ID mismatch: expected {call_id}, got {call_data.get('call_id')}")
            return False

        # Answer the call
        logger.info("📞 Answering call...")
        answer_success = self.answer_call_api(receiver_token, call_id)

        if not answer_success:
            logger.error("❌ Failed to answer call")
            return False

        logger.info("✅ Call answered")

        # Wait a moment (simulate call duration)
        await asyncio.sleep(3)

        # End the call
        logger.info("📞 Ending call...")
        end_success = self.end_call_api(caller_token, call_id)

        if not end_success:
            logger.error("❌ Failed to end call")
            return False

        logger.info("✅ Call ended")

        # Check final notifications
        logger.info(f"📊 Total notifications received: {len(self.received_notifications)}")
        for i, notification in enumerate(self.received_notifications):
            logger.info(f"  {i+1}. {notification['data'].get('type', 'unknown')}")

        logger.info("🎉 Test completed successfully!")
        return True

async def main():
    """Main test function"""
    import argparse

    parser = argparse.ArgumentParser(description='Test WebSocket call notifications')
    parser.add_argument('--caller-token', help='Caller authentication token')
    parser.add_argument('--receiver-token', help='Receiver authentication token')
    parser.add_argument('--receiver-id', type=int, help='Receiver user ID')

    args = parser.parse_args()

    tester = WebSocketCallTester()

    try:
        if args.caller_token and args.receiver_token and args.receiver_id:
            # Production testing with provided tokens
            success = await tester.test_call_flow(
                caller_token=args.caller_token,
                receiver_token=args.receiver_token,
                receiver_id=args.receiver_id
            )
        else:
            # Local testing
            success = await tester.test_call_flow()

        if success:
            logger.info("✅ All tests passed!")
            return 0
        else:
            logger.error("❌ Tests failed!")
            return 1
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)