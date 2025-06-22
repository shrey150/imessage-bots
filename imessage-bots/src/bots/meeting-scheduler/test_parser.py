#!/usr/bin/env python3
"""
Test script for the meeting parser functionality
"""

import os
import sys
from datetime import datetime

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_meeting_parser():
    """Test the meeting parser with sample inputs."""
    try:
        from meeting_parser import meeting_parser
        
        test_cases = [
            "Team standup tomorrow at 10am for 30 minutes",
            "Project review meeting Friday at 2pm with john@company.com and sarah@company.com",
            "Client call next Monday at 3pm for 1 hour on Zoom",
            "Weekly sync Thursday 10am-11am in conference room A",
            "Lunch meeting with Alex tomorrow at noon"
        ]
        
        print("🧪 Testing Meeting Parser...")
        print("=" * 50)
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\nTest {i}: {test_case}")
            print("-" * 30)
            
            try:
                meeting = meeting_parser.parse_meeting_request(test_case)
                
                if meeting:
                    print(f"✅ Parsed successfully:")
                    print(f"   Title: {meeting.title}")
                    print(f"   Start: {meeting.start_datetime}")
                    print(f"   End: {meeting.end_datetime}")
                    print(f"   Attendees: {meeting.attendees}")
                    print(f"   Location: {meeting.location}")
                    
                    # Validate the meeting
                    is_valid, error_msg = meeting_parser.validate_meeting_details(meeting)
                    if is_valid:
                        print(f"   ✅ Validation: Passed")
                    else:
                        print(f"   ❌ Validation: {error_msg}")
                else:
                    print("❌ Failed to parse meeting")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 Testing complete!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed and .env is configured")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_meeting_parser() 