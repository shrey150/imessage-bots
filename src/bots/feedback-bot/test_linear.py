#!/usr/bin/env python3
"""
Test script for Linear integration functionality.
Run this to test Linear API connection and issue creation.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config
from models import FeedbackType, StructuredFeedback, CrossChatInsight
from linear_integration import feedback_triager

async def test_linear_connection():
    """Test Linear API connection."""
    print("Testing Linear API connection...")
    
    if not config.ENABLE_LINEAR_INTEGRATION:
        print("❌ Linear integration is disabled in config")
        return False
    
    if not config.LINEAR_API_KEY:
        print("❌ LINEAR_API_KEY not configured")
        return False
    
    try:
        # Test getting teams
        teams = await feedback_triager.linear_client.get_teams()
        if teams:
            print(f"✅ Found {len(teams)} Linear teams:")
            for team in teams[:3]:  # Show first 3 teams
                print(f"   - {team['name']} ({team['key']})")
            
            # Test getting team ID
            team_id = await feedback_triager.linear_client.get_team_id()
            if team_id:
                print(f"✅ Target team ID: {team_id}")
                return True
            else:
                print("❌ Could not determine target team ID")
                return False
        else:
            print("❌ No teams found or API connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Linear connection: {e}")
        return False

async def test_feedback_formatting():
    """Test feedback formatting with GPT-4o."""
    print("\nTesting feedback formatting...")
    
    # Create sample feedback items
    sample_feedback = [
        {
            "feedback": StructuredFeedback(
                feedback_type=FeedbackType.BUG_REPORT,
                summary="App crashes when opening notifications",
                raw_message="Hey, the app keeps crashing every time I try to open my notifications. It's super annoying and happens like 3-4 times a day. I'm on iPhone 15 Pro.",
                timestamp=datetime.now()
            ),
            "chat_info": {
                "total_questions": 2,
                "conversation_length": 5,
                "user_profile": {
                    "engagement_level": "engaged",
                    "total_feedback_items": 3,
                    "feedback_types": {"bug_report": 2, "feature_request": 1}
                }
            }
        },
        {
            "feedback": StructuredFeedback(
                feedback_type=FeedbackType.FEATURE_REQUEST,
                summary="Want ability to schedule messages",
                raw_message="It would be amazing if I could schedule messages to be sent later. Like if I'm working late but don't want to bother people until morning.",
                timestamp=datetime.now()
            ),
            "chat_info": {
                "total_questions": 1,
                "conversation_length": 3,
                "user_profile": {
                    "engagement_level": "new",
                    "total_feedback_items": 1,
                    "feedback_types": {"feature_request": 1}
                }
            }
        }
    ]
    
    # Create sample cross-chat insight
    sample_insights = {
        "notification_issues": CrossChatInsight(
            feedback_type=FeedbackType.BUG_REPORT,
            theme="notification_issues",
            frequency_count=3,
            affected_chats=2,
            severity_level="high"
        )
    }
    
    try:
        formatted_issues = await feedback_triager.format_feedback_for_linear(
            sample_feedback, 
            sample_insights
        )
        
        if formatted_issues:
            print(f"✅ Successfully formatted {len(formatted_issues)} issues:")
            for i, issue in enumerate(formatted_issues, 1):
                print(f"\n   Issue #{i}:")
                print(f"   Title: {issue.get('title', 'N/A')}")
                print(f"   Type: {issue.get('type', 'N/A')}")
                print(f"   Priority: {issue.get('priority', 'N/A')}")
                print(f"   Description: {issue.get('description', 'N/A')[:100]}...")
            return True
        else:
            print("❌ No issues were formatted")
            return False
            
    except Exception as e:
        print(f"❌ Error formatting feedback: {e}")
        return False

async def test_issue_creation():
    """Test creating a single issue in Linear."""
    print("\nTesting Linear issue creation...")
    
    try:
        team_id = await feedback_triager.linear_client.get_team_id()
        if not team_id:
            print("❌ Could not get team ID")
            return False
        
        # Create a test issue
        test_title = f"Test Issue - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        test_description = """
# Test Issue from Feedback Bot

This is a test issue created by the feedback bot Linear integration.

## Details
- **Created**: Automated test
- **Type**: Test
- **Priority**: Low

## Next Steps
- [ ] Verify the issue was created correctly
- [ ] Delete this test issue if not needed

*This issue was created automatically to test the Linear integration.*
"""
        
        created_issue = await feedback_triager.linear_client.create_issue(
            title=test_title,
            description=test_description,
            team_id=team_id,
            priority=4  # Low priority
        )
        
        if created_issue:
            print(f"✅ Successfully created test issue:")
            print(f"   ID: {created_issue['identifier']}")
            print(f"   Title: {created_issue['title']}")
            print(f"   URL: {created_issue['url']}")
            return True
        else:
            print("❌ Failed to create test issue")
            return False
            
    except Exception as e:
        print(f"❌ Error creating test issue: {e}")
        return False

async def main():
    """Run all Linear integration tests."""
    print("🧪 Testing Linear Integration for Feedback Bot")
    print("=" * 50)
    
    # Test configuration
    print(f"Configuration:")
    print(f"  - Linear integration: {'enabled' if config.ENABLE_LINEAR_INTEGRATION else 'disabled'}")
    print(f"  - API key configured: {'yes' if config.LINEAR_API_KEY else 'no'}")
    print(f"  - Target team: {config.LINEAR_TEAM_KEY or 'auto-select first team'}")
    print("")
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Connection
    if await test_linear_connection():
        tests_passed += 1
    
    # Test 2: Formatting (only if connection works)
    if tests_passed > 0:
        if await test_feedback_formatting():
            tests_passed += 1
    else:
        print("⏭️  Skipping formatting test (connection failed)")
    
    # Test 3: Issue creation (only if previous tests pass)
    if tests_passed == 2:
        print("\n⚠️  The next test will create a real issue in Linear.")
        response = input("Do you want to create a test issue? (y/N): ")
        if response.lower() in ['y', 'yes']:
            if await test_issue_creation():
                tests_passed += 1
        else:
            print("⏭️  Skipping issue creation test")
            total_tests = 2  # Adjust total since we're skipping
    else:
        print("⏭️  Skipping issue creation test (previous tests failed)")
        total_tests = 2
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Linear integration is working correctly.")
    else:
        print("❌ Some tests failed. Check the configuration and try again.")
        
    return tests_passed == total_tests

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 