# CLI Overview

The iMessage Bot Framework includes a powerful command-line interface (CLI) to help you create, manage, and develop bots efficiently.

## Installation

The CLI is automatically available when you install the framework:

```bash
# Install framework
pip install imessage-bot-framework

# Verify CLI is available
imessage-bot --help
```

## Available Commands

### `create` - Create New Bot Project

Creates a new bot project with all necessary files and configuration.

```bash
imessage-bot create my-awesome-bot
```

**Options:**
- `--template` - Choose project template (basic, ai, command)
- `--with-api` - Include custom API endpoints
- `--with-database` - Include database integration
- `--no-examples` - Skip example code

**Examples:**
```bash
# Basic bot
imessage-bot create simple-bot

# AI-powered bot with API
imessage-bot create ai-bot --template ai --with-api

# Command bot with database
imessage-bot create command-bot --template command --with-database
```

### `version` - Show Version Information

Displays framework version and system information.

```bash
imessage-bot version
```

**Output:**
```
iMessage Bot Framework v1.0.0
Python: 3.9.7
FastAPI: 0.104.1
Platform: macOS-13.6-arm64
```

### `dev` - Development Tools

Development utilities for testing and debugging bots.

```bash
# Run development server with auto-reload
imessage-bot dev run main.py

# Test bot without BlueBubbles
imessage-bot dev test

# Validate bot configuration
imessage-bot dev validate
```

### `config` - Configuration Management

Manage bot configuration and environment settings.

```bash
# Show current configuration
imessage-bot config show

# Set configuration value
imessage-bot config set BLUEBUBBLES_PASSWORD "new-password"

# Generate template .env file
imessage-bot config init
```

## Quick Start Workflow

Here's the typical workflow using the CLI:

### 1. Create New Project

```bash
# Create a new bot project
imessage-bot create my-chat-bot
cd my-chat-bot
```

This creates:
```
my-chat-bot/
├── main.py              # Main bot file
├── config.py            # Configuration management
├── .env.example         # Environment template
├── .gitignore           # Git ignore rules
├── README.md            # Project documentation
└── requirements.txt     # Dependencies
```

### 2. Configure Environment

```bash
# Generate .env file from template
imessage-bot config init

# Edit configuration
nano .env
```

### 3. Test Bot

```bash
# Validate configuration
imessage-bot dev validate

# Test bot functionality (without BlueBubbles)
imessage-bot dev test
```

### 4. Run Bot

```bash
# Development mode with auto-reload
imessage-bot dev run main.py

# Production mode
python main.py
```

## Project Templates

### Basic Template

Simple bot with message handling:

```python
from imessage_bot_framework import Bot

bot = Bot("Basic Bot")

@bot.on_message
def handle_message(message):
    return f"Hello! You said: {message.text}"

if __name__ == "__main__":
    bot.run()
```

### AI Template

Bot with AI integration setup:

```python
from imessage_bot_framework import Bot
import openai
import os

bot = Bot("AI Bot")

openai.api_key = os.getenv("OPENAI_API_KEY")

@bot.on_message
def ai_chat(message):
    if message.text.startswith("ai "):
        prompt = message.text[3:]
        # AI integration code here
        return "AI response placeholder"
    return None

if __name__ == "__main__":
    bot.run()
```

### Command Template

Bot with structured command handling:

```python
from imessage_bot_framework import Bot
from imessage_bot_framework.decorators import only_from_me

bot = Bot("Command Bot")

COMMANDS = {
    "ping": lambda: "pong! 🏓",
    "time": lambda: datetime.now().strftime("%H:%M:%S"),
    "help": lambda: "Available commands: ping, time, help"
}

@bot.on_message
def handle_commands(message):
    command = message.text.lower()
    if command in COMMANDS:
        return COMMANDS[command]()
    return None

@bot.on_message
@only_from_me()
def admin_commands(message):
    if message.text == "!status":
        return "Bot is running!"
    return None

if __name__ == "__main__":
    bot.run()
```

## Development Mode

The CLI includes development tools for faster iteration:

### Auto-Reload

```bash
# Watch for file changes and auto-restart
imessage-bot dev run main.py --reload
```

### Mock Testing

```bash
# Test bot handlers without BlueBubbles
imessage-bot dev test --message "hello"
```

This simulates a message and shows what the bot would respond.

### Configuration Validation

```bash
# Check if all required environment variables are set
imessage-bot dev validate

# Check specific configuration
imessage-bot dev validate --check bluebubbles
```

## Configuration Management

### Environment Templates

```bash
# Generate .env from template
imessage-bot config init

# Generate with specific template
imessage-bot config init --template production
```

### Configuration Commands

```bash
# Show all configuration
imessage-bot config show

# Show specific values
imessage-bot config show BLUEBUBBLES_PASSWORD

# Set values
imessage-bot config set DEBUG true
imessage-bot config set BLUEBUBBLES_PASSWORD "new-password"

# Remove values
imessage-bot config unset DEBUG
```

## Advanced Usage

### Custom Templates

Create your own project templates:

```bash
# Create template directory
mkdir ~/.imessage-bot-templates/my-template

# Use custom template
imessage-bot create new-bot --template ~/.imessage-bot-templates/my-template
```

### Batch Operations

```bash
# Create multiple bots
for name in bot1 bot2 bot3; do
    imessage-bot create $name --template basic
done

# Update all bot configurations
find . -name ".env" -exec imessage-bot config update {} \;
```

### Integration with CI/CD

```bash
# Validate in CI pipeline
imessage-bot dev validate --strict

# Test all bots
imessage-bot dev test --all --format json
```

## Global Configuration

The CLI stores global settings in `~/.imessage-bot/config.json`:

```json
{
    "default_template": "basic",
    "auto_reload": true,
    "default_port": 8000,
    "bluebubbles_url": "http://localhost:1234"
}
```

Manage global config:
```bash
# Show global config
imessage-bot config global

# Set global defaults
imessage-bot config global set default_template ai
imessage-bot config global set default_port 8080
```

## Troubleshooting

### Common Issues

**Command not found:**
```bash
# Ensure framework is installed
pip show imessage-bot-framework

# Reinstall CLI
pip install --force-reinstall imessage-bot-framework
```

**Permission errors:**
```bash
# Fix permissions on macOS/Linux
chmod +x $(which imessage-bot)

# Run with python if needed
python -m imessage_bot_framework.cli --help
```

**Configuration issues:**
```bash
# Reset configuration
imessage-bot config reset

# Use absolute paths
imessage-bot create /full/path/to/my-bot
```

### Debug Mode

Enable verbose output for troubleshooting:

```bash
# Verbose output
imessage-bot --verbose create test-bot

# Debug mode
imessage-bot --debug dev run main.py
```

## See Also

- [Project Creation](project-creation.md) - Detailed project creation guide
- [Development Tools](development-tools.md) - Advanced development features
- [Quick Start](../getting-started/quick-start.md) - Manual bot creation
- [Examples](../examples/) - Complete bot examples 