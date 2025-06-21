import logging
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from models import MeetingDetails
from config import config

logger = logging.getLogger(__name__)

# Google Calendar API scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']

class GoogleCalendarManager:
    """Manages Google Calendar operations."""
    
    def __init__(self):
        self.service = None
        self.credentials = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Calendar API."""
        try:
            creds = None
            
            # The file token.json stores the user's access and refresh tokens.
            if os.path.exists(config.GOOGLE_TOKEN_FILE):
                creds = Credentials.from_authorized_user_file(config.GOOGLE_TOKEN_FILE, SCOPES)
            
            # If there are no (valid) credentials available, let the user log in.
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(config.GOOGLE_CREDENTIALS_FILE):
                        logger.error(f"Google credentials file not found: {config.GOOGLE_CREDENTIALS_FILE}")
                        return
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        config.GOOGLE_CREDENTIALS_FILE, SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                with open(config.GOOGLE_TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
            
            self.credentials = creds
            self.service = build('calendar', 'v3', credentials=creds)
            logger.info("Successfully authenticated with Google Calendar")
            
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Calendar: {e}")
            self.service = None
    
    def create_meeting(self, meeting: MeetingDetails, chat_participants: Optional[List[str]] = None) -> Optional[str]:
        """
        Create a meeting in Google Calendar.
        
        Args:
            meeting: MeetingDetails object with meeting information
            chat_participants: List of chat participants to invite
            
        Returns:
            Meeting URL or None if creation fails
        """
        if not self.service:
            logger.error("Google Calendar service not available")
            return None
        
        try:
            # Prepare attendees list
            attendees = []
            
            # Add attendees from meeting details
            for attendee in meeting.attendees:
                if '@' in attendee:  # Email address
                    attendees.append({'email': attendee})
                else:  # Name only - we can't invite without email
                    logger.warning(f"Cannot invite attendee without email: {attendee}")
            
            # Add chat participants if provided
            if chat_participants:
                for participant in chat_participants:
                    if '@' in participant:
                        attendees.append({'email': participant})
            
            # Create event object
            event = {
                'summary': meeting.title,
                'location': meeting.location,
                'description': meeting.description or f"Meeting created via iMessage bot",
                'start': {
                    'dateTime': meeting.start_datetime.isoformat(),
                    'timeZone': 'America/Los_Angeles',  # You might want to make this configurable
                },
                'end': {
                    'dateTime': meeting.end_datetime.isoformat(),
                    'timeZone': 'America/Los_Angeles',
                },
                'attendees': attendees,
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                        {'method': 'popup', 'minutes': 10},       # 10 minutes before
                    ],
                },
                'conferenceData': self._create_meet_link() if not meeting.location or 'zoom' not in meeting.location.lower() else None,
            }
            
            # Create the event
            event = self.service.events().insert(
                calendarId=config.GOOGLE_CALENDAR_ID,
                body=event,
                conferenceDataVersion=1 if event.get('conferenceData') else 0
            ).execute()
            
            meeting_url = event.get('htmlLink')
            logger.info(f"Successfully created meeting: {meeting.title}")
            logger.info(f"Meeting URL: {meeting_url}")
            
            return meeting_url
            
        except Exception as e:
            logger.error(f"Failed to create meeting: {e}")
            return None
    
    def _create_meet_link(self) -> Dict[str, Any]:
        """Create a Google Meet conference link for the meeting."""
        return {
            'createRequest': {
                'requestId': f"meet-{datetime.now().timestamp()}",
                'conferenceSolutionKey': {
                    'type': 'hangoutsMeet'
                }
            }
        }
    
    def list_upcoming_meetings(self, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        List upcoming meetings from the calendar.
        
        Args:
            max_results: Maximum number of meetings to return
            
        Returns:
            List of meeting dictionaries
        """
        if not self.service:
            logger.error("Google Calendar service not available")
            return []
        
        try:
            now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
            
            events_result = self.service.events().list(
                calendarId=config.GOOGLE_CALENDAR_ID,
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            meetings = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                meetings.append({
                    'title': event.get('summary', 'No Title'),
                    'start': start,
                    'url': event.get('htmlLink'),
                    'location': event.get('location', 'No Location')
                })
            
            return meetings
            
        except Exception as e:
            logger.error(f"Failed to list meetings: {e}")
            return []
    
    def check_availability(self, start_time: datetime, end_time: datetime) -> bool:
        """
        Check if the user is available during the specified time.
        
        Args:
            start_time: Meeting start time
            end_time: Meeting end time
            
        Returns:
            True if available, False if busy
        """
        if not self.service:
            logger.error("Google Calendar service not available")
            return True  # Assume available if we can't check
        
        try:
            # Query for busy times
            body = {
                'timeMin': start_time.isoformat() + 'Z',
                'timeMax': end_time.isoformat() + 'Z',
                'items': [{'id': config.GOOGLE_CALENDAR_ID}]
            }
            
            freebusy_result = self.service.freebusy().query(body=body).execute()
            busy_times = freebusy_result['calendars'][config.GOOGLE_CALENDAR_ID].get('busy', [])
            
            return len(busy_times) == 0
            
        except Exception as e:
            logger.error(f"Failed to check availability: {e}")
            return True  # Assume available if we can't check

# Global calendar manager instance
calendar_manager = GoogleCalendarManager() 