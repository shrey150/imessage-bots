# 🤖 Gork Bot

A sarcastic and snarky bot inspired by Grok that explains previous messages with wit and humor. Gork Bot integrates with iMessage via BlueBubbles and uses GPT-4o to generate entertaining, sarcastic explanations of previous messages.

## ✨ Features

- **Sarcastic Explanations**: Explains previous messages with Grok's characteristic wit and humor
- **Context Awareness**: Uses recent conversation history for better explanations
- **Trigger-based**: Only responds when explicitly called with `@gork`
- **GPT-4o Powered**: Uses the latest OpenAI model for intelligent responses
- **iMessage Integration**: Works seamlessly with BlueBubbles for iMessage
- **Memory Management**: Automatically manages conversation history

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- Poetry for dependency management
- BlueBubbles server setup and running
- OpenAI API key

### Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd imessage-bots/gork-bot
   ```

2. **Install dependencies**:
   ```bash
   poetry install
   ```

3. **Set up environment variables**:
   Create a `.env` file in the gork-bot directory:
   ```env
   # OpenAI Configuration
   OPENAI_API_KEY=your-openai-api-key-here
   
   # BlueBubbles Configuration
   BLUEBUBBLES_SERVER_URL=http://localhost:1234
   BLUEBUBBLES_PASSWORD=your-bluebubbles-password
   
   # Chat Configuration - The specific chat GUID where the bot should respond
   CHAT_GUID=iMessage;+;+1234567890
   
   # Optional Configuration
   HOST=0.0.0.0
   PORT=8002
   DEBUG=false
   ```

4. **Run the bot**:
   ```bash
   poetry run python main.py
   ```

## 📖 Usage

### Basic Usage

Simply mention `@gork` followed by what you want explained about the previous message:

```
Person A: "I think pineapple belongs on pizza"
Person B: "@gork explain why this is controversial"
```

Gork Bot will then provide a sarcastic, witty explanation of the previous message.

### Example Commands

- `@gork explain what they meant`
- `@gork why is this funny`
- `@gork what's the context here`
- `@gork break this down for me`
- `@gork what's wrong with this statement`

### How It Works

1. **Message Monitoring**: Gork Bot listens to messages only in the configured chat (CHAT_GUID)
2. **History Tracking**: Keeps track of recent messages with their GUIDs for context and reactions
3. **Trigger Detection**: Activates only when a message starts with `@gork`
4. **Message Reaction**: Reacts to the previous message with the ‼️ (emphasize) emoji to mark what it's explaining
5. **Context Analysis**: Analyzes the previous message and recent conversation
6. **Sarcastic Response**: Uses GPT-4o to generate a witty, Grok-style explanation

## 🛠️ Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | Your OpenAI API key | - | ✅ |
| `BLUEBUBBLES_SERVER_URL` | BlueBubbles server URL | `http://localhost:1234` | ✅ |
| `BLUEBUBBLES_PASSWORD` | BlueBubbles server password | - | ✅ |
| `CHAT_GUID` | Specific chat GUID where bot responds | - | ✅ |
| `HOST` | Server host | `0.0.0.0` | ❌ |
| `PORT` | Server port | `8002` | ❌ |
| `DEBUG` | Debug mode | `false` | ❌ |

### Bot Configuration

- **Trigger Phrase**: `@gork` (hardcoded)
- **Model**: GPT-4o
- **Message History**: Last 10 messages per chat (24-hour TTL)
- **Response Style**: Sarcastic, witty, inspired by Grok

## 🔧 Development

### Project Structure

```
gork-bot/
├── main.py              # FastAPI application and webhook handling
├── config.py            # Configuration management
├── models.py            # Pydantic data models
├── conversation_state.py # Chat history management
├── gork_ai.py          # OpenAI integration for sarcastic responses
├── pyproject.toml      # Poetry configuration
└── README.md           # This file
```

### Running in Development

```bash
# Install dependencies
poetry install

# Run with auto-reload
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8002
```

### Testing

The bot includes a health check endpoint:

```bash
curl http://localhost:8002/
```

And a stats endpoint:

```bash
curl http://localhost:8002/stats
```

## 🚀 Deployment

### Using Poetry

```bash
poetry run python main.py
```

### Using Docker (optional)

Create a `Dockerfile` in the gork-bot directory:

```dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Configure poetry and install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev

# Copy application code
COPY . .

# Expose port
EXPOSE 8002

# Run the application
CMD ["poetry", "run", "python", "main.py"]
```

## 🔍 API Endpoints

- `GET /` - Health check and bot status
- `POST /webhook` - BlueBubbles webhook endpoint
- `GET /stats` - Bot statistics and metrics

## 🎯 Grok Personality

Gork Bot embodies the following characteristics:

- **Witty and Sarcastic**: Sharp humor without being mean-spirited
- **Slightly Rebellious**: Questions conventions and norms
- **Pop Culture Savvy**: Makes references to movies, TV, and internet culture
- **Observant**: Points out human behavioral patterns
- **Entertaining**: Prioritizes being amusing while being informative
- **Dry Humor**: Uses understated, deadpan comedy

## 🐛 Troubleshooting

### Common Issues

1. **Bot not responding**:
   - Check if the message starts with `@gork`
   - Verify BlueBubbles webhook is configured correctly
   - Check logs for errors

2. **OpenAI API errors**:
   - Verify your API key is correct and has credits
   - Check rate limits

3. **BlueBubbles connection issues**:
   - Ensure BlueBubbles server is running
   - Verify server URL and password

### Logs

Enable debug logging by setting `DEBUG=true` in your `.env` file.

## 📝 License

This project is part of the iMessage bots collection. See the main repository for license information.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 🎉 Examples

Here are some example interactions:

**Example 1:**
```
User A: "I'm going to start waking up at 5 AM every day"
User B: "@gork explain why this won't work"
Gork Bot: "🤖 *Grok's Analysis* 📝

Ah yes, the classic 5 AM resolution! Let me break down this ambitious proclamation for you. This is what humans call 'productivity theater' - the delightful ritual where someone declares they'll become a morning person overnight, usually after watching one too many LinkedIn influencer videos about 'winning the day before it starts.'

The beautiful irony? They're announcing this grand life transformation at 11 PM while scrolling through their phone in bed. Statistics suggest this noble endeavor will last approximately 3.7 days before reality crashes into their snooze button like a caffeinated freight train. But hey, points for optimism! 🌅"
```

**Example 2:**
```
User A: "Just ordered 20 chicken nuggets for myself"
User B: "@gork what does this say about them"
Gork Bot: "🤖 *Grok's Analysis* 📝

Ah, the classic 20-piece nugget order - truly a masterclass in self-awareness and portion control! 🍗 This is what we call 'aggressive honesty' in food ordering. While others pretend they're sharing their 'family meal,' this person has courageously admitted they possess the appetite of a small velociraptor.

Twenty nuggets suggests either: a) they've given up on societal expectations entirely (admirable), b) they're stress-eating and nuggets are their emotional support animal, or c) they've discovered the mathematical sweet spot where the nugget-to-sauce ratio achieves perfect harmony.

Either way, this is someone who knows what they want and isn't afraid to face the McDonald's cashier with unwavering eye contact. Respect! 🫡"
```

Ready to add some sarcastic wit to your group chats! 🤖✨ 