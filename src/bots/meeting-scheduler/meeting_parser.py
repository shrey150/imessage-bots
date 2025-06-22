import logging
import json
from typing import Optional
from datetime import datetime, timedelta
from dateutil import parser as date_parser
from openai import OpenAI
from models import MeetingDetails
from config import config

logger = logging.getLogger(__name__)

class MeetingParser:
    """Parses natural language meeting requests using OpenAI."""
    
    def __init__(self):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.OPENAI_MODEL
    
    def parse_meeting_request(self, text: str) -> Optional[MeetingDetails]:
        """
        Parse a natural language meeting request into structured data.
        
        Args:
            text: The natural language meeting request
            
        Returns:
            MeetingDetails object or None if parsing fails
        """
        try:
            system_prompt = """You are a meeting scheduler assistant. Your job is to extract meeting details from natural language requests and return them as structured JSON.

Current date and time: {current_time}

Extract the following information:
- title: Meeting title/subject
- description: Optional detailed description
- start_datetime: Start date and time (ISO format)
- end_datetime: End date and time (ISO format)
- attendees: List of email addresses or names mentioned
- location: Meeting location (physical or virtual)

Rules:
1. If no specific time is mentioned, default to the next business hour (9 AM - 5 PM)
2. If no duration is specified, default to 1 hour
3. If date is relative (e.g., "tomorrow", "next week"), calculate the actual date
4. If no date is specified, assume today or the next business day
5. Extract email addresses from the text as attendees
6. If location mentions "Zoom", "Teams", "Meet", etc., include that in location

Return ONLY valid JSON in this exact format:
{{
    "title": "string",
    "description": "string or null",
    "start_datetime": "YYYY-MM-DDTHH:MM:SS",
    "end_datetime": "YYYY-MM-DDTHH:MM:SS",
    "attendees": ["email1@example.com", "name2"],
    "location": "string or null"
}}""".format(current_time=datetime.now().isoformat())

            user_prompt = f"Parse this meeting request: {text}"

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=300,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = response.choices[0].message.content.strip()
            logger.info(f"OpenAI response: {result}")
            
            # Parse the JSON response
            meeting_data = json.loads(result)
            
            # Convert datetime strings to datetime objects
            start_datetime = date_parser.parse(meeting_data["start_datetime"])
            end_datetime = date_parser.parse(meeting_data["end_datetime"])
            
            # Create MeetingDetails object
            meeting = MeetingDetails(
                title=meeting_data["title"],
                description=meeting_data.get("description"),
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                attendees=meeting_data.get("attendees", []),
                location=meeting_data.get("location")
            )
            
            logger.info(f"Successfully parsed meeting: {meeting.title}")
            return meeting
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing meeting request: {e}")
            return None
    
    def validate_meeting_details(self, meeting: MeetingDetails) -> tuple[bool, str]:
        """
        Validate meeting details for common issues.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        now = datetime.now()
        
        # Check if meeting is in the past
        if meeting.start_datetime < now:
            return False, "Meeting start time cannot be in the past"
        
        # Check if end time is after start time
        if meeting.end_datetime <= meeting.start_datetime:
            return False, "Meeting end time must be after start time"
        
        # Check if meeting duration is reasonable (not more than 8 hours)
        duration = meeting.end_datetime - meeting.start_datetime
        if duration > timedelta(hours=8):
            return False, "Meeting duration cannot exceed 8 hours"
        
        # Check if meeting is too far in the future (more than 1 year)
        if meeting.start_datetime > now + timedelta(days=365):
            return False, "Meeting cannot be scheduled more than 1 year in advance"
        
        return True, ""

# Global meeting parser instance
meeting_parser = MeetingParser() 