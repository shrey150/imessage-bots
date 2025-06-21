# Meeting Scheduler Bot 📅

An intelligent meeting scheduler bot for iMessage via BlueBubbles. This bot listens for the `!schedule` command and uses OpenAI GPT-4o to parse natural language meeting requests, then creates calendar events in Google Calendar.

## Features

- **Natural Language Processing**: Uses OpenAI GPT-4o to understand meeting requests in plain English
- **Google Calendar Integration**: Automatically creates calendar events with Google Meet links
- **Smart Scheduling**: Validates meeting times and checks for calendar conflicts
- **BlueBubbles Integration**: Seamlessly works with BlueBubbles server for iMessage delivery
- **Flexible Commands**: Supports various meeting formats and time expressions
- **Group Chat Support**: Works in both individual and group chats

## Prerequisites

1. **BlueBubbles Server**: Set up and running with webhook support
2. **OpenAI API Key**: GPT-4o access required
3. **Google Calendar API**: Credentials and OAuth setup
4. **Python 3.13+**: For running the FastAPI application

## Installation

1. **Install Dependencies**:
   ```bash
   cd imessage-bots/src/bots/meeting-scheduler
   pip install -r requirements.txt
   ```

2. **Google Calendar Setup**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable the Google Calendar API
   - Create credentials (OAuth 2.0 Client ID) for a desktop application
   - Download the credentials JSON file and save as `credentials.json`

3. **Environment Configuration**:
   ```bash
   cp ../env.example .env
   ```
   
   Edit `.env` with your actual values:
   ```bash
   OPENAI_API_KEY="your-openai-api-key-here"
   BLUEBUBBLES_SERVER_URL="http://localhost:1234"
   BLUEBUBBLES_PASSWORD="your-server-password"
   GOOGLE_CREDENTIALS_FILE="credentials.json"
   GOOGLE_TOKEN_FILE="token.json"
   GOOGLE_CALENDAR_ID="primary"
   HOST="0.0.0.0"
   PORT="8001"
   DEBUG="true"
   ```

## Usage

1. **Start the Bot**:
   ```bash
   python main.py
   ```
   Or with uvicorn directly:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8001 --reload
   ```

2. **First Run - Google OAuth**:
   - On first startup, the bot will open a browser window for Google OAuth
   - Sign in with your Google account and grant calendar permissions
   - The bot will save the token for future use

3. **Configure BlueBubbles Webhook**:
   - Open your BlueBubbles server interface
   - Navigate to webhooks configuration
   - Add webhook URL: `http://your-bot-server:8001/webhook`
   - Enable for "new-message" events

4. **Use the Bot**:
   Send messages starting with `!schedule` followed by your meeting request:
   
   **Examples:**
   ```
   !schedule Team standup tomorrow at 10am for 30 minutes
   
   !schedule Project review meeting Friday at 2pm with john@company.com and sarah@company.com
   
   !schedule Client call next Monday at 3pm for 1 hour on Zoom
   
   !schedule Weekly sync Thursday 10am-11am in conference room A
   
   !schedule Lunch meeting with Alex tomorrow at noon
   ```

## API Endpoints

- `GET /`: Health check and bot statistics
- `POST /webhook`: BlueBubbles webhook handler
- `GET /stats`: Detailed bot and calendar statistics

## How It Works

### Command Processing Flow
1. **Trigger Detection**: Bot listens for messages starting with `!schedule`
2. **Natural Language Parsing**: OpenAI GPT-4o extracts meeting details
3. **Validation**: Checks for conflicts and validates meeting parameters
4. **Calendar Creation**: Creates Google Calendar event with Google Meet link
5. **Confirmation**: Sends success message with calendar link

### Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   iMessage      │◄──►│  BlueBubbles     │◄──►│  Meeting        │
│   (User)        │    │  Server          │    │  Scheduler Bot  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
                                               ┌─────────────────┐
                                               │  OpenAI GPT-4o  │
                                               │  Meeting Parser │
                                               └─────────────────┘
                                                        │
                                               ┌─────────────────┐
                                               │  Google         │
                                               │  Calendar API   │
                                               └─────────────────┘
```

## Configuration Options

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `OPENAI_API_KEY` | *Required* | Your OpenAI API key |
| `BLUEBUBBLES_SERVER_URL` | `http://localhost:1234` | BlueBubbles server URL |
| `BLUEBUBBLES_PASSWORD` | *Required* | BlueBubbles server password |
| `GOOGLE_CREDENTIALS_FILE` | `credentials.json` | Google OAuth credentials file |
| `GOOGLE_TOKEN_FILE` | `token.json` | Google OAuth token storage |
| `GOOGLE_CALENDAR_ID` | `primary` | Calendar ID to use |
| `HOST` | `0.0.0.0` | FastAPI server host |
| `PORT` | `8001` | FastAPI server port |
| `DEBUG` | `false` | Enable debug logging |

## Natural Language Examples

The bot understands various ways to express meeting details:

**Time Expressions:**
- "tomorrow at 10am"
- "next Friday at 2:30pm"
- "Monday morning"
- "in 2 hours"
- "at 3pm for 30 minutes"

**Attendee Formats:**
- "with john@company.com"
- "invite sarah@example.com and mike@company.com"
- "including the team leads"

**Location/Platform:**
- "on Zoom"
- "in conference room A"
- "via Google Meet"
- "at the office"

## Troubleshooting

### Common Issues

1. **"Configuration error: OPENAI_API_KEY environment variable is required"**
   - Set your OpenAI API key in the `.env` file

2. **"Google credentials file not found"**
   - Download credentials from Google Cloud Console
   - Save as `credentials.json` in the bot directory

3. **"Failed to authenticate with Google Calendar"**
   - Check your Google Cloud project has Calendar API enabled
   - Ensure credentials file is valid
   - Delete `token.json` and re-authenticate

4. **Bot not responding to !schedule commands**
   - Check webhook configuration in BlueBubbles
   - Verify bot server is accessible from BlueBubbles server
   - Check logs for error messages

5. **"Meeting start time cannot be in the past"**
   - The bot validates meeting times - ensure you're scheduling future meetings
   - Check your system timezone settings

### Debugging

Enable debug logging:
```bash
export DEBUG=true
```

Check bot health:
```bash
curl http://localhost:8001/
```

View bot statistics:
```bash
curl http://localhost:8001/stats
```

## Development

### Project Structure
```
imessage-bots/src/bots/meeting-scheduler/
├── main.py                 # FastAPI application
├── config.py              # Configuration management
├── models.py              # Pydantic data models
├── conversation_state.py  # Conversation state management
├── meeting_parser.py      # OpenAI integration for parsing
├── google_calendar.py     # Google Calendar API integration
├── pyproject.toml         # Dependencies
├── requirements.txt       # Alternative dependency format
├── setup.py               # Automated setup script
├── test_parser.py         # Testing utility
└── README.md             # This file

imessage-bots/src/bots/
└── env.example            # Shared environment configuration template
```

### Key Components

- **FastAPI App**: Handles webhooks and HTTP endpoints
- **Meeting Parser**: Uses OpenAI to extract structured data from natural language
- **Google Calendar Manager**: Creates and manages calendar events
- **Conversation Manager**: Tracks conversation state across messages
- **BlueBubbles Client**: Sends responses back through iMessage

## Security Considerations

- Store API keys securely in environment variables
- Use HTTPS in production
- Consider rate limiting for webhook endpoints
- Respect Google's API usage limits and quotas
- Validate all user inputs before processing

## Examples in Action

**User**: `!schedule Team standup tomorrow at 10am for 30 minutes with john@company.com`

**Bot Response**:
```
✅ Meeting created successfully!

📝 **Team standup**
🕐 December 15, 2024 at 10:00 AM - 10:30 AM
👥 Attendees: john@company.com

🔗 [View in Calendar](https://calendar.google.com/calendar/event?...)
```

**User**: `!schedule Client presentation Friday at 2pm on Zoom`

**Bot Response**:
```
✅ Meeting created successfully!

📝 **Client presentation**
🕐 December 20, 2024 at 02:00 PM - 03:00 PM
📍 Zoom

🔗 [View in Calendar](https://calendar.google.com/calendar/event?...)
```

## License

This project is for educational and personal use. Please respect platform terms of service and API usage limits.

---

Ready to schedule some meetings? 📅✨ 