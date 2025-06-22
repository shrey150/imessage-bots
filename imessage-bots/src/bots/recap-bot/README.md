# 📋 Recap Bot

An intelligent iMessage bot that summarizes unread messages in group chats using AI. Never miss important conversations again!

## ✨ Features

- **Message-Count Recaps**: Analyze a specific number of recent messages (e.g., last 50, 100, or 200 messages)
- **AI-Powered Summaries**: Uses OpenAI GPT-4o to generate intelligent recaps
- **Personal Control**: Only you can trigger recaps using `!recap`
- **Flexible Message Counts**: Supports 1-500 messages - defaults to 50 messages
- **Detailed Analysis**: Shows participants, time range, key points, and full summary
- **Always Available**: Works regardless of read/unread status - perfect for catching up after opening chats
- **Multiple Formats**: Supports both Poetry and pip for dependency management

## 🚀 Quick Start

### 1. Setup

Run the automated setup script:

```bash
python setup.py
```

This will:
- Create a `.env` file with your configuration
- Install all dependencies
- Validate your setup

### 2. Manual Setup (Alternative)

If you prefer manual setup:

1. **Install Dependencies**:
   ```bash
   # Using Poetry (recommended)
   poetry install
   
   # Or using pip
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   Create a `.env` file with:
   ```env
   # BlueBubbles Configuration
   BLUEBUBBLES_SERVER_URL=http://localhost:1234
   BLUEBUBBLES_PASSWORD=your_password
   
   # OpenAI Configuration
   OPENAI_API_KEY=your_openai_api_key
   OPENAI_MODEL=gpt-4o
   
   # Bot Configuration (optional)
   RECAP_TRIGGER_PHRASE=!recap
   RECAP_PORT=8002
   MAX_MESSAGES_TO_ANALYZE=200
   MAX_SUMMARY_LENGTH=500
   ```

### 3. Run the Bot

```bash
# Using Poetry
poetry run python main.py

# Or directly with Python
python main.py
```

The bot will start on `http://127.0.0.1:8002`

### 4. Configure BlueBubbles

Add a webhook in BlueBubbles pointing to:
```
http://127.0.0.1:8002/webhook
```

## 📱 How to Use

### Basic Usage
- **`!recap`** - Get a summary of the last 50 messages (default)
- **`!recap 100`** - Get a summary of the last 100 messages  
- **`!recap 25`** - Get a summary of the last 25 messages
- **`!recap 200`** - Get a summary of the last 200 messages

### How It Works
1. **Send a recap command**: Use `!recap` with optional message count in any chat
2. **Bot analyzes messages**: Fetches and processes the specified number of recent messages
3. **Get your summary**: The bot provides:
   - Time range of the messages
   - List of participants
   - Number of messages analyzed
   - AI-generated summary
   - Key points extracted

### Example Usage

```
You: !recap 50

Bot: 📊 Analyzing the last 50 messages... This may take a moment.

Bot: 📋 Recap of 50 messages (Alice, Bob, Charlie) from December 15 from 2:30PM to 4:45PM: The group planned a weekend mountain trip with Alice suggesting Friday evening departure to avoid traffic. Bob confirmed he can drive his 5-person car and Charlie shared the Airbnb link with 3 PM check-in. They decided on staying in the cabin instead of camping due to cold weather.
```

### Message Count Examples
- `!recap` or `!recap 50` - Last 50 messages (default)
- `!recap 25` - Last 25 messages
- `!recap 100` - Last 100 messages
- `!recap 150` - Last 150 messages
- `!recap 200` - Last 200 messages
- `!recap 300` - Last 300 messages (max 500)

## 🛠️ Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `RECAP_TRIGGER_PHRASE` | `!recap` | Command to trigger recap |
| `RECAP_PORT` | `8002` | Port for the bot server |
| `MAX_MESSAGES_TO_ANALYZE` | `200` | Maximum messages to analyze |
| `MAX_SUMMARY_LENGTH` | `500` | Maximum tokens for AI summary |
| `OPENAI_API_KEY` | Required | OpenAI API key for message summarization |

## 🔧 API Endpoints

- `GET /` - Health check and bot status
- `POST /webhook` - BlueBubbles webhook endpoint
- `GET /stats` - Bot statistics and chat tracking info
- `POST /mark-read/{chat_guid}` - Manually mark a chat as read

## 📊 How It Works

1. **Webhook Monitoring**: The bot receives all messages via BlueBubbles webhooks
2. **Message-Count Fetching**: When you send `!recap [count]`, the bot:
   - Parses the message count (defaults to 50 if not specified)
   - Fetches the specified number of most recent messages from BlueBubbles API
   - Filters out your own messages (no need to recap what you said)
   - Sends conversation to OpenAI for summarization
   - Formats and sends the recap

## 🔒 Privacy & Security

- **Your Messages Only**: Only you (identified by BlueBubbles isFromMe flag) can trigger recaps
- **Local Storage**: Chat states stored locally in `chat_states.json`
- **API Security**: Uses BlueBubbles password authentication
- **OpenAI**: Conversations sent to OpenAI for summarization (review their privacy policy)

## 🐛 Troubleshooting

### Bot not responding to `!recap`
- Verify BlueBubbles webhook is configured correctly
- Check that BlueBubbles correctly sets isFromMe flag for your messages
- Check bot logs for errors

### "Unable to fetch messages"
- Verify BlueBubbles server URL and password
- Check BlueBubbles API is accessible
- Ensure chat GUID is correct

### OpenAI errors
- Verify API key is valid and has credits
- Check if you have access to GPT-4o model
- Review rate limits

### No messages found
- Try a larger message count (e.g., `!recap 100` or `!recap 200`)
- Ensure the chat has recent messages
- Check if the chat GUID is correct

## 📝 Development

### Project Structure
```
recap-bot/
├── main.py              # FastAPI application
├── config.py            # Configuration management
├── models.py            # Data models
├── message_tracker.py   # Message counting and state
├── message_summarizer.py # AI summarization
├── setup.py             # Automated setup
├── requirements.txt     # Dependencies
├── pyproject.toml       # Poetry configuration
└── README.md           # Documentation
```

### Running Tests
```bash
# Test configuration
python config.py

# Test individual components
python -c "from message_tracker import MessageTracker; mt = MessageTracker(); print('Tracker OK')"
```

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📄 License

This project is part of the iMessageBot collection. 