#!/usr/bin/env python
"""
Simple Channel Layer Test Script
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ezeyway.settings')
django.setup()

from channels.layers import get_channel_layer
import asyncio

async def test_channel_layer():
    """Test channel layer functionality"""
    print("Testing channel layer...")

    channel_layer = get_channel_layer()
    print(f"Channel layer: {channel_layer}")
    print(f"Channel layer type: {type(channel_layer)}")

    if channel_layer:
        print("✅ Channel layer is available")

        # Test sending a message
        try:
            await channel_layer.group_send(
                "user_2",
                {
                    'type': 'test_message',
                    'message': 'Hello from channel layer test'
                }
            )
            print("✅ Message sent to group user_2")
        except Exception as e:
            print(f"❌ Failed to send message: {e}")
    else:
        print("❌ Channel layer is None")

if __name__ == "__main__":
    asyncio.run(test_channel_layer())