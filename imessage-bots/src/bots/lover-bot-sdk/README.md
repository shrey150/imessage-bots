# Lover Bot SDK

An AI girlfriend bot built with the **iMessage Bot Framework** that provides context-aware romantic messaging with reactive responses.

## 🌟 Features

- **Context-Aware Messaging**: Understands conversation state, user mood, and relationship dynamics
- **Initial Greeting**: Sends one welcome message when first started
- **Reactive Responses**: Only responds when you text first - no automatic spam
- **Admin Commands**: Control the bot with special commands
- **FastAPI Integration**: Web endpoints for monitoring and manual control
- **Conversation Memory**: Remembers context across messages for better responses

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install with Poetry (recommended)
poetry install

# Or install the SDK dependency directly
pip install -e /path/to/imessage-bot-framework
```

### 2. Configure Environment

Copy `.env.example` to `.env` and configure:

```bash
# BlueBubbles Server
BLUEBUBBLES_SERVER_URL=http://localhost:1234
BLUEBUBBLES_PASSWORD=your-actual-password

# Bot Configuration  
CHAT_GUID=your-chat-guid-here
DEBUG=false

# OpenAI API
OPENAI_API_KEY=your-openai-api-key

# Personality
LOVER_NAME=Alex
USER_NAME=babe
```

### 3. Run the Bot

```bash
poetry run python main.py
```

## 🤖 How It Works

### Messaging Behavior
- **Initial Message**: Sends one greeting when the bot first starts
- **Reactive Only**: Only responds when you send a message first
- **No Automatic Messages**: Won't spam you with unsolicited messages
- **Context-Aware**: Each response considers conversation history and your mood

### Admin Commands

Send these commands from your phone to control the bot:

- `!lover` or `!lover status` - Show bot status and stats
- `!lover send` - Manually trigger a message
- `!lover reset` - Reset conversation memory

### Web Interface

The bot runs a web server with these endpoints:

- `GET /` - Health check and status
- `GET /stats` - Detailed statistics  
- `POST /send-message` - Manually trigger a message

## 📁 Project Structure

```
lover-bot-sdk/
├── main.py              # Main bot application (SDK-based)
├── config.py            # Configuration management
├── lover_ai.py          # AI response generation
├── conversation_state.py # Conversation context management
├── models.py            # Data models
├── pyproject.toml       # Poetry dependencies
├── README.md            # This file
└── COMPARISON.md        # Comparison with original bot
```

## 🔄 Switching Between Versions

If you want to run the original lover bot instead:

```bash
# Stop this SDK version (Ctrl+C)
cd ../lover-bot
python main.py  # Original version with automatic messaging
```

Both versions use the same port (8080) so only one can run at a time.

## 🆚 Comparison with Original

See [COMPARISON.md](COMPARISON.md) for a detailed comparison showing:
- 26% less code (250 vs 340 lines)
- 90% less webhook handling boilerplate  
- 80% less message parsing code
- 60% less error handling code
- Cleaner admin commands and API integration

## 🛠️ Development

### Running in Debug Mode

```bash
# Enable debug logging
export DEBUG=true
poetry run python main.py
```

### Testing the Bot

1. Start the bot
2. Send a message to the configured chat
3. The bot will respond contextually
4. Use admin commands to control behavior

### Key Differences from Original

- **Reactive Only**: No automatic messaging intervals
- **SDK-Based**: Uses iMessage Bot Framework for cleaner code
- **Better Context**: Enhanced conversation state management
- **Simpler Setup**: Fewer configuration options to manage

## 📝 License

Same as the iMessage Bot Framework project. 