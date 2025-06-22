#!/usr/bin/env python3
"""
Test script for the iMessage Bot Framework SDK.

This script tests basic functionality without requiring BlueBubbles.
"""

import sys
import os

# Add the SDK to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all core components can be imported."""
    print("Testing imports...")
    
    try:
        from imessage_bot_framework import Bot, Message, Chat, State
        print("✅ Core imports successful")
    except ImportError as e:
        print(f"❌ Core import failed: {e}")
        return False
    
    try:
        from imessage_bot_framework.decorators import command, contains, regex
        print("✅ Decorator imports successful")
    except ImportError as e:
        print(f"❌ Decorator import failed: {e}")
        return False
    
    return True

def test_bot_creation():
    """Test bot creation and basic functionality."""
    print("\nTesting bot creation...")
    
    try:
        from imessage_bot_framework import Bot
        
        bot = Bot("Test Bot", port=8999, debug=True)
        print("✅ Bot creation successful")
        
        # Test handler registration
        @bot.on_message
        def test_handler(message):
            return "Test response"
        
        print("✅ Handler registration successful")
        return True
        
    except Exception as e:
        print(f"❌ Bot creation failed: {e}")
        return False

def test_state_management():
    """Test state management functionality."""
    print("\nTesting state management...")
    
    try:
        from imessage_bot_framework import State
        
        # Create state with test file
        state = State("test_state.json")
        
        # Test basic operations
        state.set("test_key", "test_value")
        value = state.get("test_key")
        assert value == "test_value", f"Expected 'test_value', got '{value}'"
        
        # Test increment
        count = state.increment("counter")
        assert count == 1, f"Expected 1, got {count}"
        
        count = state.increment("counter", 5)
        assert count == 6, f"Expected 6, got {count}"
        
        # Test list operations
        state.append("items", "item1")
        state.append("items", "item2")
        items = state.get("items")
        assert len(items) == 2, f"Expected 2 items, got {len(items)}"
        
        # Cleanup
        os.remove("test_state.json")
        
        print("✅ State management tests passed")
        return True
        
    except Exception as e:
        print(f"❌ State management test failed: {e}")
        # Cleanup on failure
        if os.path.exists("test_state.json"):
            os.remove("test_state.json")
        return False

def test_decorators():
    """Test decorator functionality."""
    print("\nTesting decorators...")
    
    try:
        from imessage_bot_framework.decorators import command, contains, regex
        from imessage_bot_framework.core.message import Message
        
        # Mock bot config
        bot_config = {
            "bluebubbles_url": "http://localhost:1234",
            "bluebubbles_password": "test"
        }
        
        # Test command decorator
        @command("!test")
        def test_command(message):
            return "Command worked!"
        
        # Create mock message
        mock_message = Message(
            text="!test hello",
            sender="test_user",
            chat_guid="test_chat",
            raw_data={"isFromMe": False, "dateCreated": 0},
            bot_config=bot_config
        )
        
        result = test_command(mock_message)
        assert result == "Command worked!", f"Expected 'Command worked!', got '{result}'"
        
        # Test contains decorator
        @contains("pizza")
        def pizza_handler(message):
            return "Pizza detected!"
        
        pizza_message = Message(
            text="I love pizza",
            sender="test_user", 
            chat_guid="test_chat",
            raw_data={"isFromMe": False, "dateCreated": 0},
            bot_config=bot_config
        )
        
        result = pizza_handler(pizza_message)
        assert result == "Pizza detected!", f"Expected 'Pizza detected!', got '{result}'"
        
        print("✅ Decorator tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Decorator test failed: {e}")
        return False

def test_message_creation():
    """Test message object creation and methods."""
    print("\nTesting message creation...")
    
    try:
        from imessage_bot_framework.core.message import Message
        
        bot_config = {
            "bluebubbles_url": "http://localhost:1234",
            "bluebubbles_password": "test"
        }
        
        message = Message(
            text="Hello world",
            sender="test_user",
            chat_guid="test_chat_guid",
            raw_data={
                "isFromMe": False,
                "dateCreated": 1640995200000,  # 2022-01-01
                "guid": "test_message_guid"
            },
            bot_config=bot_config
        )
        
        assert message.text == "Hello world"
        assert message.sender == "test_user"
        assert message.chat_guid == "test_chat_guid"
        assert message.is_from_me == False
        assert message.guid == "test_message_guid"
        
        print("✅ Message creation tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Message creation test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Running iMessage Bot Framework SDK Tests\n")
    
    tests = [
        test_imports,
        test_bot_creation,
        test_state_management,
        test_decorators,
        test_message_creation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()  # Add spacing between tests
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The SDK is working correctly.")
        return 0
    else:
        print("❌ Some tests failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 