#!/usr/bin/env python3
"""CLI for the iMessage Bot Framework."""

import argparse
import sys
from pathlib import Path
from typing import Optional

from ..core.bot import Bot


def create_bot_template(name: str, directory: Optional[str] = None) -> None:
    """Create a new bot template."""
    if directory:
        bot_dir = Path(directory) / name
    else:
        bot_dir = Path(name)
    
    bot_dir.mkdir(parents=True, exist_ok=True)
    
    # Create main.py
    main_py = bot_dir / "main.py"
    main_py.write_text(f'''"""
{name} - An iMessage bot built with the iMessage Bot Framework.
"""

from imessage_bot_framework import Bot

# Create your bot
bot = Bot("{name}")

@bot.on_message
def hello_handler(message):
    """Handle hello messages."""
    if message.text.lower().startswith("!hello"):
        return f"Hello {{message.sender}}! 👋"

@bot.command("ping")
def ping_handler(message):
    """Respond to ping commands."""
    return "Pong! 🏓"

if __name__ == "__main__":
    bot.run()
''')
    
    # Create config.py
    config_py = bot_dir / "config.py"
    config_py.write_text('''"""Configuration for the bot."""

import os
from typing import Optional

# BlueBubbles Configuration
BLUEBUBBLES_HOST: str = os.getenv("BLUEBUBBLES_HOST", "localhost")
BLUEBUBBLES_PORT: int = int(os.getenv("BLUEBUBBLES_PORT", "1234"))
BLUEBUBBLES_PASSWORD: Optional[str] = os.getenv("BLUEBUBBLES_PASSWORD")

# Bot Configuration
BOT_PORT: int = int(os.getenv("BOT_PORT", "8000"))
BOT_HOST: str = os.getenv("BOT_HOST", "0.0.0.0")

# OpenAI (optional)
OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
''')
    
    # Create .env.example
    env_example = bot_dir / ".env.example"
    env_example.write_text('''# BlueBubbles Configuration
BLUEBUBBLES_HOST=localhost
BLUEBUBBLES_PORT=1234
BLUEBUBBLES_PASSWORD=your_password_here

# Bot Configuration
BOT_PORT=8000
BOT_HOST=0.0.0.0

# OpenAI (optional)
OPENAI_API_KEY=your_openai_key_here
''')
    
    # Create pyproject.toml
    pyproject_toml = bot_dir / "pyproject.toml"
    pyproject_toml.write_text(f'''[tool.poetry]
name = "{name.lower().replace(' ', '-')}"
version = "0.1.0"
description = "An iMessage bot built with the iMessage Bot Framework"
authors = ["Your Name <your.email@example.com>"]
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.8"
imessage-bot-framework = "^0.1.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.0.0"
black = "^23.0.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
''')
    
    # Create README.md
    readme_md = bot_dir / "README.md"
    readme_md.write_text(f'''# {name}

An iMessage bot built with the [iMessage Bot Framework](https://github.com/your-username/imessage-bot-framework).

## Setup

1. Install dependencies:
   ```bash
   poetry install
   ```

2. Copy the environment file and configure:
   ```bash
   cp .env.example .env
   # Edit .env with your BlueBubbles configuration
   ```

3. Run the bot:
   ```bash
   poetry run python main.py
   ```

## Commands

- `!hello` - Say hello
- `!ping` - Get a pong response

## Configuration

Edit `config.py` to customize your bot's behavior.
''')
    
    print(f"✅ Created bot template '{name}' in {bot_dir}")
    print(f"📁 Next steps:")
    print(f"   cd {bot_dir}")
    print(f"   poetry install")
    print(f"   cp .env.example .env")
    print(f"   # Edit .env with your configuration")
    print(f"   poetry run python main.py")


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="iMessage Bot Framework CLI",
        prog="imessage-bot"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new bot")
    create_parser.add_argument("name", help="Name of the bot")
    create_parser.add_argument(
        "--directory", "-d",
        help="Directory to create the bot in (default: current directory)"
    )
    
    # Version command
    version_parser = subparsers.add_parser("version", help="Show version")
    
    args = parser.parse_args()
    
    if args.command == "create":
        create_bot_template(args.name, args.directory)
    elif args.command == "version":
        from .. import __version__
        print(f"iMessage Bot Framework v{__version__}")
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main() 