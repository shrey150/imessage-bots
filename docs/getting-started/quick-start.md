# Quick Start

Build your first iMessage bot in under 10 minutes! This guide walks you through creating a simple but functional bot.

## Your First Bot

Let's create a bot that responds to messages and provides some useful commands.

### 1. Create Project Structure

```bash
# Create a new directory
mkdir my-first-bot
cd my-first-bot

# Create the main bot file
touch main.py

# Create environment file
touch .env
```

### 2. Configure Environment

Edit `.env` with your BlueBubbles settings:

```bash
# .env
BLUEBUBBLES_SERVER_URL=http://localhost:1234
BLUEBUBBLES_PASSWORD=your-server-password
CHAT_GUID=your-chat-guid-here
DEBUG=true
```

### 3. Write Your Bot

Create your bot in `main.py`:

```python
# main.py
import os
from dotenv import load_dotenv
from imessage_bot_framework import Bot
from imessage_bot_framework.decorators import only_from_me

# Load environment variables
load_dotenv()

# Create bot instance
bot = Bot("My First Bot", debug=True)

@bot.on_message
def handle_message(message):
    """Handle all incoming messages."""
    text = message.text.lower()
    
    # Simple greeting
    if any(word in text for word in ["hello", "hi", "hey"]):
        return f"Hello! Nice to hear from you!"
    
    # Echo command
    if text.startswith("echo "):
        return text[5:]  # Remove "echo " prefix
    
    # Help command
    if text in ["help", "commands"]:
        return """Available commands:
• hello/hi/hey - Get a greeting
• echo <message> - Echo your message
• help - Show this help
• time - Get current time
• !admin - Admin commands (owner only)"""
    
    # Time command
    if text == "time":
        from datetime import datetime
        return f"Current time: {datetime.now().strftime('%I:%M %p')}"
    
    # Default response for unrecognized messages
    return f"I received: '{message.text}'\nSay 'help' for available commands!"

@bot.on_message
@only_from_me()
def admin_commands(message):
    """Admin-only commands (only you can use these)."""
    if message.text.startswith("!admin"):
        parts = message.text.split()
        
        if len(parts) == 1:
            return """Admin Commands:
• !admin status - Show bot status
• !admin send <message> - Send message to chat
• !admin restart - Restart bot"""
        
        elif parts[1] == "status":
            return f"✅ Bot is running\n🔧 Debug: {bot.debug}\n📡 Server: Ready"
        
        elif parts[1] == "send" and len(parts) > 2:
            message_text = " ".join(parts[2:])
            chat_guid = os.getenv("CHAT_GUID")
            bot.send_to_chat(f"[Admin Message] {message_text}", chat_guid)
            return "✅ Message sent!"
    
    return None  # Let other handlers process the message

# Add custom API endpoints
@bot.app.get("/status")
async def bot_status():
    """Public endpoint to check bot status."""
    return {
        "status": "running",
        "bot_name": "My First Bot",
        "version": "1.0.0"
    }

@bot.app.post("/send")
async def send_message(data: dict):
    """API endpoint to send messages."""
    text = data.get("message", "")
    chat_guid = data.get("chat_guid") or os.getenv("CHAT_GUID")
    
    if not text or not chat_guid:
        return {"error": "Missing message or chat_guid"}
    
    success = bot.send_to_chat(text, chat_guid)
    return {"success": success, "message": "Message sent" if success else "Failed to send"}

if __name__ == "__main__":
    print("🤖 Starting My First Bot...")
    print("💬 Send messages to test the bot!")
    print("🌐 API available at http://localhost:8000")
    
    # Validate environment
    if not os.getenv("BLUEBUBBLES_PASSWORD"):
        print("⚠️  Warning: BLUEBUBBLES_PASSWORD not set")
    if not os.getenv("CHAT_GUID"):
        print("⚠️  Warning: CHAT_GUID not set")
    
    bot.run()
```

### 4. Run Your Bot

```bash
# Install dependencies first
pip install python-dotenv  # for .env file support

# Run the bot
python main.py
```

You should see output like:
```
🤖 Starting My First Bot...
💬 Send messages to test the bot!
🌐 API available at http://localhost:8000
INFO:     Started server process
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 5. Test Your Bot

Send messages to your configured chat to test:

- **"hello"** → Bot responds with greeting
- **"echo test message"** → Bot echoes "test message"
- **"help"** → Shows available commands
- **"time"** → Shows current time
- **"!admin status"** → Admin status (only works for you)

### 6. Test API Endpoints

Your bot also has web endpoints:

```bash
# Check bot status
curl http://localhost:8000/status

# Send a message via API
curl -X POST http://localhost:8000/send \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello from API!", "chat_guid": "your-chat-guid"}'
```

## Understanding Your Bot

Let's break down what you just built:

### Message Handlers

```python
@bot.on_message
def handle_message(message):
    # This handles ALL incoming messages
    return "Optional response"
```

### Admin-Only Commands

```python
@bot.on_message
@only_from_me()
def admin_commands(message):
    # This only responds to YOUR messages
    return "Admin response"
```

### Custom API Endpoints

```python
@bot.app.get("/endpoint")
async def custom_endpoint():
    # FastAPI endpoint for web access
    return {"data": "value"}
```

### Message Object Properties

```python
def handle_message(message):
    message.text        # The message content
    message.sender      # Who sent it
    message.chat_guid   # Which chat it came from
    message.is_from_me  # True if you sent it
    message.timestamp   # When it was sent
```

## Next Steps

Now that you have a working bot, explore these features:

### 1. Add More Commands

```python
@bot.on_message
def more_commands(message):
    text = message.text.lower()
    
    if text == "joke":
        return "Why do programmers prefer dark mode? Because light attracts bugs! 🐛"
    
    if text.startswith("weather "):
        city = text[8:]
        return f"I'd tell you the weather in {city}, but I need a weather API first! 🌤️"
```

### 2. Add State Management

```python
from imessage_bot_framework import State

state = State("bot_data.json")

@bot.on_message
def counter(message):
    if message.text == "count":
        current = state.get("count", 0)
        new_count = current + 1
        state.set("count", new_count)
        return f"Count: {new_count}"
```

### 3. Add AI Integration

```python
import openai

@bot.on_message
def ai_chat(message):
    if message.text.startswith("ai "):
        prompt = message.text[3:]
        # Call OpenAI API
        response = openai.ChatCompletion.create(...)
        return response.choices[0].message.content
```

## Common Patterns

### Command Pattern

```python
COMMANDS = {
    "ping": lambda: "pong! 🏓",
    "uptime": lambda: "I've been running for...",
    "version": lambda: "Bot v1.0.0"
}

@bot.on_message
def command_handler(message):
    if message.text in COMMANDS:
        return COMMANDS[message.text]()
```

### Regex Pattern

```python
import re

@bot.on_message
def regex_handler(message):
    # Match phone numbers
    if re.match(r'\d{3}-\d{3}-\d{4}', message.text):
        return "I see you shared a phone number!"
```

## Troubleshooting

### Bot Not Responding

1. **Check webhook configuration** in BlueBubbles server
2. **Verify chat GUID** is correct
3. **Check bot logs** for errors

### Permission Issues

1. **Admin commands not working**: Ensure `@only_from_me()` decorator
2. **Messages not sending**: Check BlueBubbles password and URL

### Development Tips

```python
# Add debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test without sending messages
def test_handler():
    from imessage_bot_framework.core.message import Message
    fake_message = Message("test", "sender", "chat", {}, {})
    result = handle_message(fake_message)
    print(f"Bot would respond: {result}")
```

## Resources

- **[Project Structure](project-structure.md)** - Organize larger bots
- **[Message Handling](../core-concepts/message-handling.md)** - Advanced message processing
- **[Examples](../examples/)** - More bot examples
- **[API Reference](../api-reference/)** - Detailed documentation

---

**Congratulations!** 🎉 You've built your first iMessage bot. Ready to build something more advanced? Check out our [examples](../examples/) for inspiration! 