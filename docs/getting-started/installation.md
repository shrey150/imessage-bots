# Installation

This guide will help you install and set up the iMessage Bot Framework for development.

## Prerequisites

Before installing the framework, ensure you have:

- **Python 3.8 or higher**
- **macOS** (required for BlueBubbles server)
- **BlueBubbles Server** installed and configured

## Installation Methods

### Option 1: Using Poetry (Recommended)

Poetry provides the best development experience with dependency management.

```bash
# Clone the repository
git clone https://github.com/your-org/imessage-bot-framework.git
cd imessage-bot-framework

# Install with Poetry
poetry install

# Activate the virtual environment
poetry shell
```

### Option 2: Using pip

```bash
# Install from PyPI (when published)
pip install imessage-bot-framework

# Or install from source
git clone https://github.com/your-org/imessage-bot-framework.git
cd imessage-bot-framework
pip install -e .
```

### Option 3: Development Installation

For contributing to the framework:

```bash
# Clone and install in development mode
git clone https://github.com/your-org/imessage-bot-framework.git
cd imessage-bot-framework

# Install with development dependencies
poetry install --with dev

# Run tests to verify installation
poetry run pytest
```

## BlueBubbles Server Setup

The framework requires a BlueBubbles server to send and receive iMessages.

### 1. Install BlueBubbles Server

Download and install BlueBubbles server from [bluebubbles.app](https://bluebubbles.app).

### 2. Configure Server

1. **Open BlueBubbles Server**
2. **Set Server Password**: Choose a secure password
3. **Enable API Access**: Turn on "Enable REST API"
4. **Configure Webhooks**: Set webhook URL to your bot's endpoint
5. **Note Server URL**: Usually `http://localhost:1234`

### 3. Get Chat GUID

To send messages to specific chats, you need the chat GUID:

1. Open **Messages.app** on your Mac
2. Start a conversation with your target contact/group
3. In BlueBubbles server, go to **Chats** tab
4. Find your conversation and copy the **GUID**

## Environment Configuration

Create a `.env` file in your project root:

```bash
# BlueBubbles Configuration
BLUEBUBBLES_SERVER_URL=http://localhost:1234
BLUEBUBBLES_PASSWORD=your-server-password

# Bot Configuration
BOT_NAME=My Awesome Bot
DEBUG=true

# For specific bots
CHAT_GUID=your-chat-guid-here
```

## Verify Installation

Create a simple test bot to verify everything works:

```python
# test_bot.py
from imessage_bot_framework import Bot

bot = Bot("Test Bot", debug=True)

@bot.on_message
def test_handler(message):
    return f"Bot is working! You said: {message.text}"

if __name__ == "__main__":
    print("Starting test bot...")
    bot.run()
```

Run the test bot:

```bash
python test_bot.py
```

You should see:
```
Starting test bot...
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

## Troubleshooting

### Common Issues

**ModuleNotFoundError**: Ensure you're in the correct virtual environment
```bash
poetry shell  # or activate your venv
```

**BlueBubbles Connection Error**: Check server URL and password
```bash
curl http://localhost:1234/api/v1/ping?password=your-password
```

**Port Already in Use**: Change the bot port
```python
bot = Bot("My Bot", port=8001)
```

### Getting Help

- Check the [troubleshooting guide](../best-practices/debugging.md)
- Join our Discord community
- Create an issue on GitHub

## Next Steps

Now that you have the framework installed:

1. **[Quick Start Guide](quick-start.md)** - Build your first bot
2. **[Project Structure](project-structure.md)** - Understand the framework layout
3. **[Examples](../examples/)** - See practical implementations

## CLI Tools

The framework includes helpful CLI tools:

```bash
# Create a new bot project
imessage-bot create my-new-bot

# Check version
imessage-bot version

# Get help
imessage-bot --help
```

---

**Ready to build your first bot?** Continue to the [Quick Start Guide](quick-start.md)! 