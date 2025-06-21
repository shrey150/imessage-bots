# Resume Roast Bot 🔥

A snarky resume roasting chatbot for iMessage via BlueBubbles. This bot prompts users for their LinkedIn profile URLs and generates witty, conversational roasts based on their professional experience.

## Features

- **Smart Conversation Flow**: Tracks user state and progressively gets snarkier when waiting for LinkedIn URLs
- **LinkedIn Profile Scraping**: Extracts professional information from LinkedIn profiles
- **AI-Powered Roasting**: Uses OpenAI GPT-4o to generate personalized career roasts
- **BlueBubbles Integration**: Seamlessly works with BlueBubbles server for iMessage delivery
- **Graceful Error Handling**: Provides fallback responses when scraping or AI generation fails

## Prerequisites

1. **BlueBubbles Server**: Set up and running with webhook support
2. **OpenAI API Key**: GPT-4o access required
3. **Python 3.13+**: For running the FastAPI application

## Installation

1. **Install Dependencies**:
   ```bash
   cd src/bots/resume-roast
   pip install -e .
   ```

2. **Environment Configuration**:
   Create a `.env` file or set environment variables:
   ```bash
   export OPENAI_API_KEY="your-openai-api-key-here"
   export BLUEBUBBLES_SERVER_URL="http://localhost:1234"  # Your BlueBubbles server
   export BLUEBUBBLES_PASSWORD="your-server-password"
   export HOST="0.0.0.0"
   export PORT="8000"
   export DEBUG="true"  # Optional: enable debug logging
   ```

## Usage

1. **Start the Bot**:
   ```bash
   python main.py
   ```
   Or with uvicorn directly:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Configure BlueBubbles Webhook**:
   - Open your BlueBubbles server interface
   - Navigate to webhooks configuration
   - Add webhook URL: `http://your-bot-server:8000/webhook`
   - Enable for "new-message" events

3. **Test the Bot**:
   - Send any message to start a conversation
   - The bot will prompt for your LinkedIn profile URL
   - Provide a valid LinkedIn URL (e.g., `https://linkedin.com/in/username`)
   - Wait for your career to get roasted! 🔥

## API Endpoints

- `GET /`: Health check and bot statistics
- `POST /webhook`: BlueBubbles webhook handler
- `GET /stats`: Conversation statistics

## How It Works

### Conversation Flow
1. **Initial Contact**: User sends any message to start
2. **LinkedIn Request**: Bot asks for LinkedIn profile URL
3. **URL Validation**: Validates LinkedIn URL format
4. **Profile Scraping**: Extracts professional information
5. **Roast Generation**: Creates personalized roast using GPT-4o
6. **Delivery**: Sends roast back via iMessage

### Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   iMessage      │◄──►│  BlueBubbles     │◄──►│  Resume Roast   │
│   (User)        │    │  Server          │    │  Bot (FastAPI)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
                                               ┌─────────────────┐
                                               │  LinkedIn       │
                                               │  Profile        │
                                               │  Scraper        │
                                               └─────────────────┘
                                                        │
                                               ┌─────────────────┐
                                               │  OpenAI GPT-4o  │
                                               │  Roast          │
                                               │  Generator      │
                                               └─────────────────┘
```

## Configuration Options

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `OPENAI_API_KEY` | *Required* | Your OpenAI API key |
| `BLUEBUBBLES_SERVER_URL` | `http://localhost:1234` | BlueBubbles server URL |
| `BLUEBUBBLES_PASSWORD` | *Required* | BlueBubbles server password |
| `HOST` | `0.0.0.0` | FastAPI server host |
| `PORT` | `8000` | FastAPI server port |
| `DEBUG` | `false` | Enable debug logging |

## LinkedIn Scraping Notes

⚠️ **Important**: LinkedIn has strong anti-scraping measures. This implementation:
- Uses realistic browser headers
- Implements respectful delays
- Provides fallback responses when scraping fails
- May not work consistently due to LinkedIn's bot detection

For production use, consider:
- LinkedIn's official API
- Proxy rotation
- More sophisticated scraping techniques

## Troubleshooting

### Common Issues

1. **"Configuration error: OPENAI_API_KEY environment variable is required"**
   - Set your OpenAI API key in environment variables

2. **"Failed to send message to BlueBubbles"**
   - Check BlueBubbles server is running and accessible
   - Verify password and server URL are correct

3. **"LinkedIn locked us out"**
   - LinkedIn blocked the scraping attempt
   - The bot will send a fallback roast instead

4. **Bot not responding to messages**
   - Check webhook configuration in BlueBubbles
   - Verify bot server is accessible from BlueBubbles server
   - Check logs for error messages

### Debugging

Enable debug logging:
```bash
export DEBUG=true
```

Check bot health:
```bash
curl http://localhost:8000/
```

View conversation stats:
```bash
curl http://localhost:8000/stats
```

## Development

### Project Structure
```
src/bots/resume-roast/
├── main.py                 # FastAPI application
├── config.py              # Configuration management
├── models.py              # Pydantic data models
├── conversation_state.py  # In-memory state management
├── linkedin_scraper.py    # LinkedIn profile extraction
├── roast_generator.py     # OpenAI integration
├── pyproject.toml         # Dependencies
└── README.md             # This file
```

### Key Components

- **FastAPI App**: Handles webhooks and HTTP endpoints
- **Conversation Manager**: Tracks user states across messages
- **LinkedIn Scraper**: Extracts profile data (with anti-bot handling)
- **Roast Generator**: Creates personalized roasts using GPT-4o
- **BlueBubbles Client**: Sends responses back through iMessage

## Security Considerations

- Store API keys securely in environment variables
- Use HTTPS in production
- Consider rate limiting for webhook endpoints
- Respect LinkedIn's terms of service and robots.txt

## License

This project is for educational and personal use. Please respect platform terms of service and use responsibly.

---

Ready to roast some careers? Fire up the bot and let the professional destruction begin! 🔥💼 