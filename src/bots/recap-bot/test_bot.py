#!/usr/bin/env python3
"""Test script for the recap bot."""

import asyncio
import json
import requests
from datetime import datetime

# Configuration
BOT_URL = "http://127.0.0.1:8001"
TEST_CHAT_GUID = "test-chat-123"

def test_health_check():
    """Test the health check endpoint."""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{BOT_URL}/")
        response.raise_for_status()
        data = response.json()
        print(f"✅ Health check passed: {data['status']}")
        print(f"   Bot: {data['bot']} v{data['version']}")
        print(f"   Trigger: {data['trigger']}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_stats():
    """Test the stats endpoint."""
    print("\n🔍 Testing stats endpoint...")
    try:
        response = requests.get(f"{BOT_URL}/stats")
        response.raise_for_status()
        data = response.json()
        print(f"✅ Stats retrieved successfully")
        print(f"   Stats: {json.dumps(data['stats'], indent=2)}")
        return True
    except Exception as e:
        print(f"❌ Stats test failed: {e}")
        return False

def test_webhook_message():
    """Test sending a webhook message."""
    print("\n🔍 Testing webhook with message...")
    
    # Create a test message webhook
    webhook_data = {
        "type": "message",
        "data": {
            "guid": "test-message-123",
            "text": "This is a test message from Alice",
            "handle": {
                "address": "+1234567890",
                "displayName": "Alice"
            },
            "chat": {
                "guid": TEST_CHAT_GUID
            },
            "dateCreated": int(datetime.now().timestamp() * 1000),
            "isFromMe": False
        }
    }
    
    try:
        response = requests.post(f"{BOT_URL}/webhook", json=webhook_data)
        response.raise_for_status()
        data = response.json()
        print(f"✅ Webhook message processed: {data['status']}")
        return True
    except Exception as e:
        print(f"❌ Webhook message test failed: {e}")
        return False

def test_recap_command():
    """Test sending a recap command."""
    print("\n🔍 Testing recap command...")
    
    # Create a recap command webhook (from user)
    webhook_data = {
        "type": "message",
        "data": {
            "guid": "test-recap-123",
            "text": "!recap",
            "handle": {
                "address": "+1234567890",  # This should match YOUR_PHONE_NUMBER
                "displayName": "You"
            },
            "chat": {
                "guid": TEST_CHAT_GUID
            },
            "dateCreated": int(datetime.now().timestamp() * 1000),
            "isFromMe": True
        }
    }
    
    try:
        response = requests.post(f"{BOT_URL}/webhook", json=webhook_data)
        response.raise_for_status()
        data = response.json()
        print(f"✅ Recap command processed: {data['status']}")
        print("   Check the bot logs to see if it's processing the recap...")
        return True
    except Exception as e:
        print(f"❌ Recap command test failed: {e}")
        return False

def test_mark_read():
    """Test manually marking a chat as read."""
    print("\n🔍 Testing mark as read...")
    
    try:
        response = requests.post(f"{BOT_URL}/mark-read/{TEST_CHAT_GUID}")
        response.raise_for_status()
        data = response.json()
        print(f"✅ Mark as read successful: {data['status']}")
        print(f"   Unread count: {data['unread_count']}")
        return True
    except Exception as e:
        print(f"❌ Mark as read test failed: {e}")
        return False

def simulate_conversation():
    """Simulate a conversation with multiple messages."""
    print("\n🔍 Simulating conversation...")
    
    messages = [
        ("Alice", "Hey everyone! Are we still on for the movie tonight?"),
        ("Bob", "Yes! I already bought tickets for the 7 PM show"),
        ("Charlie", "Perfect! What time should we meet?"),
        ("Alice", "How about 6:30 PM at the theater entrance?"),
        ("Bob", "Sounds good. I'll bring some snacks"),
        ("Charlie", "Great! See you all there 🍿")
    ]
    
    for i, (sender, text) in enumerate(messages):
        webhook_data = {
            "type": "message",
            "data": {
                "guid": f"test-msg-{i}",
                "text": text,
                "handle": {
                    "address": f"+123456789{i}",
                    "displayName": sender
                },
                "chat": {
                    "guid": TEST_CHAT_GUID
                },
                "dateCreated": int((datetime.now().timestamp() + i * 60) * 1000),  # 1 minute apart
                "isFromMe": False
            }
        }
        
        try:
            response = requests.post(f"{BOT_URL}/webhook", json=webhook_data)
            response.raise_for_status()
            print(f"   📨 Sent message from {sender}")
        except Exception as e:
            print(f"   ❌ Failed to send message from {sender}: {e}")
            return False
    
    print("✅ Conversation simulation complete")
    return True

def main():
    """Run all tests."""
    print("🤖 Testing Recap Bot...\n")
    
    tests = [
        ("Health Check", test_health_check),
        ("Stats Endpoint", test_stats),
        ("Webhook Message", test_webhook_message),
        ("Conversation Simulation", simulate_conversation),
        ("Stats After Messages", test_stats),
        ("Recap Command", test_recap_command),
        ("Mark as Read", test_mark_read),
        ("Final Stats", test_stats)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        if test_func():
            passed += 1
        
        # Small delay between tests
        import time
        time.sleep(1)
    
    print(f"\n{'='*50}")
    print(f"Test Results: {passed}/{total} passed")
    print('='*50)
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️  {total - passed} tests failed")
    
    print("\n💡 Tips:")
    print("- Make sure the bot is running on http://127.0.0.1:8002")
    print("- Check your .env file has YOUR_PHONE_NUMBER set correctly")
    print("- Look at the bot logs for detailed processing information")
    print("- The recap command test requires OpenAI API to be working")

if __name__ == "__main__":
    main() 