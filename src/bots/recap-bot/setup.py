#!/usr/bin/env python3
"""Setup script for the recap bot."""

import os
import sys
from pathlib import Path

def create_env_file():
    """Create .env file with necessary environment variables."""
    env_file = Path(".env")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return
    
    print("🔧 Creating .env file...")
    
    # Get values from user
    bluebubbles_url = input("Enter BlueBubbles server URL (e.g., http://localhost:1234): ").strip()
    bluebubbles_password = input("Enter BlueBubbles password: ").strip()
    openai_api_key = input("Enter OpenAI API key: ").strip()
    
    env_content = f"""# Recap Bot Configuration

# BlueBubbles Configuration
BLUEBUBBLES_SERVER_URL={bluebubbles_url}
BLUEBUBBLES_PASSWORD={bluebubbles_password}

# OpenAI Configuration
OPENAI_API_KEY={openai_api_key}
OPENAI_MODEL=gpt-4o

# Bot Configuration (uses BlueBubbles isFromMe flag to identify your messages)
RECAP_TRIGGER_PHRASE=!recap
RECAP_HOST=127.0.0.1
RECAP_PORT=8002

# Recap Settings
MAX_MESSAGES_TO_ANALYZE=200
MAX_SUMMARY_LENGTH=500
"""
    
    with open(env_file, "w") as f:
        f.write(env_content)
    
    print("✅ .env file created successfully")

def install_dependencies():
    """Install dependencies using pip."""
    print("📦 Installing dependencies...")
    
    try:
        import subprocess
        
        # Try to use poetry first
        result = subprocess.run(["poetry", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print("Using Poetry to install dependencies...")
            subprocess.run(["poetry", "install"], check=True)
        else:
            print("Using pip to install dependencies...")
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        
        print("✅ Dependencies installed successfully")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Neither poetry nor pip found. Please install dependencies manually.")
        sys.exit(1)

def validate_config():
    """Validate the configuration."""
    print("🔍 Validating configuration...")
    
    try:
        import config
        config.validate_config()
        print("✅ Configuration is valid")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)

def main():
    """Main setup function."""
    print("🤖 Setting up Recap Bot...\n")
    
    # Create .env file
    create_env_file()
    print()
    
    # Install dependencies
    install_dependencies()
    print()
    
    # Validate configuration
    validate_config()
    print()
    
    print("🎉 Setup complete!")
    print("\nTo start the bot:")
    print("  python main.py")
    print("\nOr with Poetry:")
    print("  poetry run python main.py")
    print("\nThe bot will listen on http://127.0.0.1:8002")
    print("Make sure to configure BlueBubbles to send webhooks to this URL!")

if __name__ == "__main__":
    main() 