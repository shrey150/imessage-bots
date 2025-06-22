# 💕 Lover Bot

An AI-powered lover bot that texts you throughout the day like a caring significant other. Uses GPT-4o to generate contextual, romantic messages based on the time of day and your conversation history.

## ✨ Features

- 🤖 **AI-Powered**: Uses GPT-4o to generate natural, contextual romantic messages
- ⏰ **Automatic Messaging**: Sends loving messages every 5 minutes (configurable)
- 🎭 **Time-Aware**: Adjusts message tone based on time of day (morning, afternoon, evening, night)
- 💬 **Interactive**: Responds to your messages with appropriate romantic replies
- 📝 **Conversation Memory**: Remembers recent conversation for contextual responses
- ❤️ **Customizable**: Configure your lover's name and what they call you

## 🚀 Setup

### Prerequisites

- Python 3.8+
- Poetry
- BlueBubbles server running and configured
- OpenAI API key

### Installation

1. **Install dependencies with Poetry:**
   ```bash
   cd src/bots/lover-bot
   poetry install
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your actual values:
   - `BLUEBUBBLES_SERVER_URL`: Your BlueBubbles server URL
   - `BLUEBUBBLES_PASSWORD`: Your BlueBubbles server password
   - `CHAT_GUID`: The chat GUID where you want to receive messages
   - `OPENAI_API_KEY`: Your OpenAI API key for GPT-4o
   - `LOVER_NAME`: Your AI lover's name (default: Alex)
   - `USER_NAME`: What your AI lover calls you (default: babe)

3. **Find your Chat GUID:**
   - Send yourself a message through iMessage
   - Check your BlueBubbles server logs to find the chat GUID
   - Add this GUID to your `.env` file

### Running the Bot

```bash
poetry run python main.py
```

The bot will:
1. Send you an immediate "hello" message when it starts
2. Begin sending loving messages every 5 minutes
3. Respond to any messages you send in the configured chat

## 🎛️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BLUEBUBBLES_SERVER_URL` | BlueBubbles server URL | `http://localhost:1234` |
| `BLUEBUBBLES_PASSWORD` | BlueBubbles server password | - |
| `CHAT_GUID` | Chat GUID for messages | - |
| `MESSAGE_INTERVAL_MINUTES` | Minutes between automatic messages | `5` |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `LOVER_NAME` | Your AI lover's name | `Alex` |
| `USER_NAME` | What your lover calls you | `babe` |
| `PORT` | FastAPI server port | `8002` |
| `DEBUG` | Enable debug logging | `false` |

### Message Types

The bot generates different types of messages based on time of day:

- **Morning (5 AM - 12 PM)**: Good morning messages, motivation, starting the day together
- **Afternoon (12 PM - 5 PM)**: Check-ins, thinking of you messages, encouragement
- **Evening (5 PM - 9 PM)**: End of day messages, asking about your day
- **Night (9 PM - 5 AM)**: Goodnight messages, sweet dreams, bedtime affection

## 🔧 API Endpoints

### Health Check
```
GET /
```
Returns bot status and statistics.

### Force Send Message
```
POST /send-message
```
Forces the bot to send an immediate loving message.

### Statistics
```
GET /stats
```
Returns detailed bot statistics including message count and conversation history.

### Webhook
```
POST /webhook
```
Handles incoming BlueBubbles webhooks for message responses.

## 💡 Usage Examples

### Automatic Messages
The bot will automatically send messages like:
- "Good morning babe! ☀️ Hope you have an amazing day ahead 💕"
- "Just thinking about you 💭 Hope your day is going well! ❤️"
- "Sweet dreams babe 🌙 Love you so much ❤️"

### Interactive Responses
When you text the bot, it will respond contextually:
- You: "Had a rough day at work"
- Bot: "Aw babe, I'm sorry you had a tough day 😔 You're so strong though and I believe in you! Want to talk about it? 💕"

## 🛠️ Development

### Running in Development Mode
```bash
# Enable debug logging
echo "DEBUG=true" >> .env

# Run with auto-reload
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8002
```

### Testing
```bash
poetry run pytest
```

## 🔒 Privacy & Security

- All conversation history is stored locally
- Only the last 20 messages are kept in memory
- OpenAI API calls include conversation context but no personal identifying information
- Your chat GUID and personal information stay on your local machine

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## ⚠️ Disclaimer

This is an AI bot for entertainment purposes. Please use responsibly and be aware that:
- AI responses are generated and may not always be appropriate
- The bot uses OpenAI's API which has usage costs
- Messages are sent automatically - make sure you want regular text messages
- This is not a substitute for real human relationships! 💕 