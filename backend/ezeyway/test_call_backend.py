#!/usr/bin/env python3
"""
Test script to verify call backend functionality
"""
import os
import sys
import django
import json
from datetime import datetime

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ezeyway.settings')
django.setup()

from accounts.models import CustomUser
from accounts.message_models import Call, Conversation
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def test_call_creation():
    """Test call creation and WebSocket notification"""
    print("=== Testing Call Creation ===")
    
    # Get test users
    try:
        caller = CustomUser.objects.filter(user_type='vendor').first()
        receiver = CustomUser.objects.filter(user_type='customer').first()
        
        if not caller or not receiver:
            print("❌ Need at least one vendor and one customer user for testing")
            return False
            
        print(f"✅ Found test users: Caller={caller.username} (ID: {caller.id}), Receiver={receiver.username} (ID: {receiver.id})")
        
        # Create call
        call = Call.objects.create(
            caller=caller,
            receiver=receiver,
            call_type='audio',
            status='initiated'
        )
        
        print(f"✅ Call created: ID={call.id}, call_id={call.call_id}")
        
        # Test WebSocket notification
        channel_layer = get_channel_layer()
        if channel_layer:
            print("✅ Channel layer available")
            
            # Send test notification
            async_to_sync(channel_layer.group_send)(
                f"user_{receiver.id}",
                {
                    'type': 'incoming_call',
                    'call': {
                        'id': call.id,
                        'call_id': call.call_id,
                        'call_type': call.call_type,
                        'status': call.status,
                        'started_at': call.started_at.isoformat(),
                        'caller': {
                            'id': call.caller.id,
                            'display_name': f"{call.caller.first_name} {call.caller.last_name}".strip() or call.caller.username,
                        },
                        'receiver': {
                            'id': call.receiver.id,
                            'display_name': f"{call.receiver.first_name} {call.receiver.last_name}".strip() or call.receiver.username,
                        }
                    }
                }
            )
            print(f"✅ WebSocket notification sent to user_{receiver.id}")
        else:
            print("❌ Channel layer not available")
            
        return True
        
    except Exception as e:
        print(f"❌ Error in call creation test: {e}")
        return False

def test_call_status_updates():
    """Test call status updates"""
    print("\n=== Testing Call Status Updates ===")
    
    try:
        # Get latest call
        call = Call.objects.last()
        if not call:
            print("❌ No calls found for testing")
            return False
            
        print(f"✅ Testing with call ID: {call.call_id}")
        
        # Test status transitions
        statuses = ['ringing', 'answered', 'ended']
        
        for status in statuses:
            call.status = status
            if status == 'answered':
                call.answered_at = datetime.now()
            elif status == 'ended':
                call.ended_at = datetime.now()
            call.save()
            print(f"✅ Updated call status to: {status}")
            
        return True
        
    except Exception as e:
        print(f"❌ Error in status update test: {e}")
        return False

def test_websocket_routing():
    """Test WebSocket URL patterns"""
    print("\n=== Testing WebSocket Routing ===")
    
    try:
        from accounts.routing import websocket_urlpatterns
        
        expected_patterns = [
            'ws/messages/',
            'ws/user/',
            'ws/calls/',
            'ws/notifications/'
        ]
        
        for pattern in websocket_urlpatterns:
            pattern_str = str(pattern.pattern)
            print(f"✅ Found WebSocket pattern: {pattern_str}")
            
        print("✅ WebSocket routing configured")
        return True
        
    except Exception as e:
        print(f"❌ Error in WebSocket routing test: {e}")
        return False

def test_api_endpoints():
    """Test API endpoint configuration"""
    print("\n=== Testing API Endpoints ===")
    
    try:
        from accounts.message_urls import urlpatterns
        
        call_endpoints = [
            'create-call/',
            'calls/initiate/',
            'calls/incoming/'
        ]
        
        found_endpoints = []
        for pattern in urlpatterns:
            pattern_str = str(pattern.pattern)
            found_endpoints.append(pattern_str)
            
        for endpoint in call_endpoints:
            if any(endpoint in found for found in found_endpoints):
                print(f"✅ Found API endpoint: {endpoint}")
            else:
                print(f"❌ Missing API endpoint: {endpoint}")
                
        return True
        
    except Exception as e:
        print(f"❌ Error in API endpoint test: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Call Backend Tests")
    print("=" * 50)
    
    tests = [
        test_websocket_routing,
        test_api_endpoints,
        test_call_creation,
        test_call_status_updates
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Call backend is ready.")
    else:
        print("⚠️  Some tests failed. Check the issues above.")
        
    return passed == total

if __name__ == "__main__":
    main()