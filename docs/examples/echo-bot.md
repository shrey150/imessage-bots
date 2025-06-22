# Basic Echo Bot

A simple bot that echoes back whatever message you send to it. Perfect for learning the basics of the iMessage Bot Framework.

## Complete Code

```python
# echo_bot.py
from imessage_bot_framework import Bot

# Create the bot
bot = Bot("Echo Bot", debug=True)

@bot.on_message
def echo_handler(message):
    """Echo back the received message."""
    return f"Echo: {message.text}"

if __name__ == "__main__":
    print("🔄 Starting Echo Bot...")
    print("💬 Send any message to see it echoed back!")
    bot.run()
```

## How It Works

1. **Import the Framework**: `from imessage_bot_framework import Bot`
2. **Create Bot Instance**: `bot = Bot("Echo Bot", debug=True)`
3. **Register Handler**: `@bot.on_message` decorator registers the function
4. **Process Messages**: Function receives `message` object, returns response
5. **Start Server**: `bot.run()` starts the webhook server

## Environment Setup

Create a `.env` file:

```bash
# .env
BLUEBUBBLES_SERVER_URL=http://localhost:1234
BLUEBUBBLES_PASSWORD=your-server-password
DEBUG=true
```

## Running the Bot

```bash
# Install dependencies
pip install python-dotenv

# Run the bot
python echo_bot.py
```

You should see:
```
🔄 Starting Echo Bot...
💬 Send any message to see it echoed back!
INFO:     Started server process
INFO:     Uvicorn running on http://127.0.0.1:8000
```

## Testing

Send any message to your configured chat:
- **"Hello"** → Bot responds: **"Echo: Hello"**
- **"How are you?"** → Bot responds: **"Echo: How are you?"**
- **"🎉"** → Bot responds: **"Echo: 🎉"**

## Enhancements

### 1. Enhanced Echo with Sender Info

```python
@bot.on_message
def enhanced_echo(message):
    return f"Echo from {message.sender}: {message.text}"
```

### 2. Selective Echo (Only Echo Certain Messages)

```python
@bot.on_message
def selective_echo(message):
    # Only echo messages that start with "echo"
    if message.text.lower().startswith("echo"):
        return f"Echoed: {message.text[5:]}"  # Remove "echo " prefix
    return None  # Don't respond to other messages
```

### 3. Echo with Timestamp

```python
from datetime import datetime

@bot.on_message
def timestamped_echo(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    return f"[{timestamp}] Echo: {message.text}"
```

### 4. Echo Counter

```python
count = 0

@bot.on_message
def counting_echo(message):
    global count
    count += 1
    return f"Echo #{count}: {message.text}"
```

### 5. Echo with Message Properties

```python
@bot.on_message
def detailed_echo(message):
    details = f"""
Echo Details:
• Text: {message.text}
• From: {message.sender}
• Chat: {message.chat_guid[:20]}...
• From Me: {message.is_from_me}
• Time: {message.timestamp}
    """.strip()
    return details
```

## API Endpoint

Add a web endpoint to trigger echoes:

```python
from pydantic import BaseModel

class EchoRequest(BaseModel):
    text: str
    chat_guid: str

@bot.app.post("/echo")
async def api_echo(request: EchoRequest):
    """API endpoint to send echo messages."""
    echo_text = f"API Echo: {request.text}"
    success = bot.send_to_chat(echo_text, request.chat_guid)
    return {
        "success": success,
        "echoed_text": echo_text,
        "original": request.text
    }
```

Test the API:
```bash
curl -X POST http://localhost:8000/echo \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello from API!", "chat_guid": "your-chat-guid"}'
```

## Troubleshooting

### Bot Not Responding
1. Check BlueBubbles webhook configuration
2. Verify chat GUID is correct
3. Check server logs for errors

### Common Issues

**Issue**: No response from bot
**Solution**: Make sure handler returns a string, not None

```python
# Wrong - returns None
@bot.on_message
def broken_handler(message):
    print(message.text)  # Only prints, doesn't return

# Correct - returns string
@bot.on_message
def working_handler(message):
    return f"Echo: {message.text}"
```

**Issue**: Bot responds to its own messages
**Solution**: Check `is_from_me` property

```python
@bot.on_message
def no_self_echo(message):
    if message.is_from_me:
        return None  # Don't echo own messages
    return f"Echo: {message.text}"
```

## Next Steps

Now that you have a basic echo bot working:

1. **[Command Bot](command-bot.md)** - Add commands and logic
2. **[AI Chat Bot](ai-bot.md)** - Integrate with AI services  
3. **[Advanced Patterns](advanced-patterns.md)** - Complex bot behaviors
4. **[Custom Endpoints](../advanced/custom-endpoints.md)** - Add web APIs

## Complete Enhanced Example

Here's a more feature-rich echo bot:

```python
# enhanced_echo_bot.py
import os
from datetime import datetime
from dotenv import load_dotenv
from imessage_bot_framework import Bot
from imessage_bot_framework.decorators import only_from_me

load_dotenv()

bot = Bot("Enhanced Echo Bot", debug=True)

# Statistics
stats = {"messages_echoed": 0, "start_time": datetime.now()}

@bot.on_message
def enhanced_echo(message):
    """Enhanced echo with multiple features."""
    global stats
    
    # Don't echo own messages
    if message.is_from_me:
        return None
    
    text = message.text.lower()
    
    # Special commands
    if text == "stats":
        uptime = datetime.now() - stats["start_time"]
        return f"📊 Stats:\n• Messages echoed: {stats['messages_echoed']}\n• Uptime: {uptime}"
    
    if text == "help":
        return """🔄 Enhanced Echo Bot Commands:
• Any message - Echoed back
• stats - Show bot statistics  
• help - Show this help
• !admin - Admin commands (owner only)"""
    
    # Regular echo
    stats["messages_echoed"] += 1
    timestamp = datetime.now().strftime("%H:%M:%S")
    return f"[{timestamp}] Echo #{stats['messages_echoed']}: {message.text}"

@bot.on_message
@only_from_me()
def admin_commands(message):
    """Admin-only commands."""
    if message.text == "!admin":
        return """🔧 Admin Commands:
• !admin - Show this menu
• !reset - Reset statistics
• !info - Show bot info"""
    
    elif message.text == "!reset":
        stats["messages_echoed"] = 0
        stats["start_time"] = datetime.now()
        return "✅ Statistics reset!"
    
    elif message.text == "!info":
        return f"""🤖 Bot Information:
• Name: {bot.name}
• Debug: {bot.debug}
• Port: {bot.port}
• Config: {len(bot.config)} settings"""
    
    return None

# API endpoint for external echo
@bot.app.post("/api/echo")
async def api_echo(data: dict):
    text = data.get("text", "")
    chat_guid = data.get("chat_guid") or os.getenv("CHAT_GUID")
    
    if not text or not chat_guid:
        return {"error": "Missing text or chat_guid"}
    
    echo_text = f"API Echo: {text}"
    success = bot.send_to_chat(echo_text, chat_guid)
    
    if success:
        stats["messages_echoed"] += 1
    
    return {
        "success": success,
        "echoed": echo_text,
        "count": stats["messages_echoed"]
    }

if __name__ == "__main__":
    print("🔄 Starting Enhanced Echo Bot...")
    print("💬 Features: timestamps, statistics, admin commands, API")
    print(f"🌐 API available at http://localhost:{bot.port}/api/echo")
    bot.run()
```

This enhanced version includes:
- ✅ Message counting and statistics
- ✅ Timestamps on echoed messages  
- ✅ Help and stats commands
- ✅ Admin-only commands with `@only_from_me()`
- ✅ API endpoint for external access
- ✅ Prevents echoing own messages 