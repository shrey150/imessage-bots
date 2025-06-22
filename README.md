# 🤖 iMessage Bot Framework

A simple, flexible framework for building iMessage bots using BlueBubbles. Create powerful bots with just a few lines of Python!

## ✨ Features

- **Simple API**: Create bots with minimal code
- **Flexible Patterns**: Commands, regex, text matching, and more
- **State Management**: Built-in persistent storage
- **Middleware Support**: Add authentication, rate limiting, logging
- **Production Ready**: Built on FastAPI with proper error handling
- **Extensible**: Plugin system for advanced features

## 🚀 Quick Start

### Installation

Install using pip:
```bash
pip install imessage-bot-framework
```

Or with Poetry:
```bash
poetry add imessage-bot-framework
```

### Your First Bot

```python
from imessage_bot_framework import Bot

# Create a bot
bot = Bot("My First Bot")

# Add a simple command
@bot.on_message
def hello_handler(message):
    if message.text.startswith("!hello"):
        return "Hello there! 👋"

# Start the bot
bot.run()
```

Set your environment variables:
```bash
export BLUEBUBBLES_SERVER_URL="http://localhost:1234"
export BLUEBUBBLES_PASSWORD="your_password"
```

Run your bot and send `!hello` in any iMessage chat!

## 📚 Examples

### Command Bot with Arguments

```python
from imessage_bot_framework import Bot
from imessage_bot_framework.decorators import command

bot = Bot("Calculator Bot")

@bot.on_message
@command("!calc")
def calculator(message, args):
    try:
        result = eval(args)  # Don't do this in production!
        return f"Result: {result}"
    except:
        return "Invalid calculation"

bot.run()
```

### State Management

```python
from imessage_bot_framework import Bot, State
from imessage_bot_framework.decorators import command

bot = Bot("Counter Bot")
state = State()

@bot.on_message
@command("!count")
def increment_counter(message):
    count = state.increment(f"counter_{message.sender}")
    return f"Your count: {count}"

@bot.on_message
@command("!reset")
def reset_counter(message):
    state.set(f"counter_{message.sender}", 0)
    return "Counter reset!"

bot.run()
```

### Regex Patterns

```python
from imessage_bot_framework import Bot
from imessage_bot_framework.decorators import regex

bot = Bot("Math Bot")

@bot.on_message
@regex(r"(\d+)\s*([+\-*/])\s*(\d+)")
def math_handler(message, a, op, b):
    a, b = int(a), int(b)
    if op == '+': return f"{a} + {b} = {a + b}"
    if op == '-': return f"{a} - {b} = {a - b}"
    if op == '*': return f"{a} * {b} = {a * b}"
    if op == '/': return f"{a} / {b} = {a / b}" if b != 0 else "Cannot divide by zero!"

bot.run()
```

### Middleware Example

```python
from imessage_bot_framework import Bot
from imessage_bot_framework.decorators import command, rate_limit

bot = Bot("Protected Bot")

# Rate limiting middleware
@bot.use_middleware
def rate_limiter(message, next_handler):
    # Simple rate limiting logic here
    return next_handler(message)

# Authentication middleware
@bot.use_middleware
def auth_required(message, next_handler):
    if message.sender not in ["allowed_user@example.com"]:
        return "Access denied"
    return next_handler(message)

@bot.on_message
@command("!secret")
def secret_command(message):
    return "You have access to the secret!"

bot.run()
```

### Chat Interaction

```python
from imessage_bot_framework import Bot

bot = Bot("Chat Manager")

@bot.on_message
def chat_info(message):
    if message.text == "!info":
        participants = message.chat.get_participants()
        recent_messages = message.chat.get_messages(limit=10)
        return f"Chat has {len(participants)} participants and {len(recent_messages)} recent messages"

@bot.on_message
def broadcast(message):
    if message.text.startswith("!broadcast ") and message.is_from_me:
        msg = message.text[11:]  # Remove "!broadcast "
        # Send to multiple chats
        bot.send_to_chat(msg, "chat-guid-1")
        bot.send_to_chat(msg, "chat-guid-2")
        return "Message broadcasted!"

bot.run()
```

## 🎯 Available Decorators

### Pattern Matching
- `@command("!trigger")` - Match command triggers
- `@contains("text")` - Match messages containing text
- `@regex(r"pattern")` - Match regex patterns

### Access Control
- `@only_from_me()` - Only respond to your messages
- `@only_from_user("user@example.com")` - Restrict to specific user
- `@rate_limit(max_calls=5, window_seconds=60)` - Rate limiting

## 🗄️ State Management

The framework includes a simple but powerful state system:

```python
from imessage_bot_framework import State

state = State("my_bot_state.json")

# Basic operations
state.set("key", "value")
value = state.get("key", "default")
state.delete("key")

# Numeric operations
count = state.increment("counter")
state.increment("score", 10)

# List operations
state.append("items", "new_item")

# Conversation context
with state.conversation(user_id) as conv:
    conv.set("name", "John")
    conv.save({"age": 25, "city": "NYC"})
```

## 🛠️ CLI Tool

The framework includes a CLI tool to help you create new bots quickly:

### Create a New Bot

```bash
# Install the framework
pip install imessage-bot-framework

# Create a new bot project
imessage-bot create "My Awesome Bot"

# Or specify a directory
imessage-bot create "My Bot" --directory ~/bots/
```

This creates a complete bot project with:
- `main.py` - Your bot's main file
- `config.py` - Configuration management
- `pyproject.toml` - Poetry dependencies
- `.env.example` - Environment template
- `README.md` - Project documentation

### CLI Commands

```bash
imessage-bot create <name>     # Create a new bot
imessage-bot version           # Show framework version
```

### Using the Generated Project

```bash
cd my-awesome-bot
poetry install
cp .env.example .env
# Edit .env with your BlueBubbles configuration
poetry run python main.py
```

## 🔧 Configuration

Set these environment variables:

```bash
# Required
BLUEBUBBLES_SERVER_URL=http://localhost:1234
BLUEBUBBLES_PASSWORD=your_password

# Optional
BOT_DEBUG=true
BOT_PORT=8000
```

Or configure programmatically:

```python
bot = Bot("My Bot", port=8001, debug=True)
```

## 🏗️ Project Structure

```
my_bot/
├── main.py            # Main bot file
├── config.py          # Configuration management
├── pyproject.toml     # Poetry dependencies
├── .env               # Environment variables
├── .env.example       # Environment template
├── README.md          # Project documentation
└── bot_state.json     # Persistent state (auto-created)
```

## 📡 Deployment

### Local Development
```bash
# With Poetry
poetry run python main.py

# Or with pip
python main.py
```

### Production with Docker
```dockerfile
FROM python:3.11-slim

# Install Poetry
RUN pip install poetry

WORKDIR /app

# Copy Poetry files
COPY pyproject.toml poetry.lock* ./

# Configure Poetry and install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev

COPY . .
CMD ["python", "main.py"]
```

### Environment Variables for Production
```bash
BLUEBUBBLES_SERVER_URL=https://your-bluebubbles-server.com
BLUEBUBBLES_PASSWORD=your_secure_password
```

## 🔌 Extending with Plugins

Create custom plugins:

```python
# plugins/openai_plugin.py
import openai

class OpenAIPlugin:
    def __init__(self, api_key):
        self.client = openai.OpenAI(api_key=api_key)
    
    def chat_completion(self, prompt):
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

# Use in your bot
from plugins.openai_plugin import OpenAIPlugin

bot = Bot("AI Bot")
ai = OpenAIPlugin(api_key="your-key")

@bot.on_message
@command("!ai")
def ai_chat(message, prompt):
    response = ai.chat_completion(prompt)
    return response

bot.run()

# Add to pyproject.toml:
# [tool.poetry.dependencies]
# openai = "^1.0.0"
```

## 🐛 Debugging

Enable debug mode:

```python
bot = Bot("Debug Bot", debug=True)
```

Or set environment variable:
```bash
export BOT_DEBUG=true
```

This will show detailed logs of webhook processing, message handling, and errors.

## 📖 API Reference

### Bot Class

```python
class Bot:
    def __init__(self, name: str = "Bot", port: int = 8000, debug: bool = False)
    def on_message(self, handler: Callable) -> Callable
    def use_middleware(self, middleware: Callable) -> Callable
    def send_to_chat(self, text: str, chat_guid: str) -> bool
    def run(self, host: str = "127.0.0.1") -> None
```

### Message Class

```python
class Message:
    text: str                    # Message content
    sender: str                  # Sender identifier
    chat_guid: str              # Chat GUID
    is_from_me: bool            # True if sent by bot owner
    timestamp: datetime         # Message timestamp
    
    def reply(self, text: str) -> bool
    def send_to_chat(self, text: str, chat_guid: str = None) -> bool
    @property
    def chat(self) -> Chat      # Get Chat object
```

### Chat Class

```python
class Chat:
    guid: str                   # Chat GUID
    
    def send(self, text: str) -> bool
    def get_messages(self, limit: int = 50) -> List[Dict]
    def get_participants(self) -> List[str]
```

### State Class

```python
class State:
    def get(self, key: str, default: Any = None) -> Any
    def set(self, key: str, value: Any) -> None
    def delete(self, key: str) -> None
    def increment(self, key: str, amount: int = 1) -> int
    def append(self, key: str, value: Any) -> None
    def conversation(self, user_id: str) -> ConversationContext
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built on top of [BlueBubbles](https://bluebubbles.app/) for iMessage integration
- Powered by [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- Inspired by modern bot frameworks like Discord.py and Telegram Bot API

---

**Ready to build your first iMessage bot?** Check out our [examples](examples/) directory for more inspiration! 