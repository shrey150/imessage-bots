#!/usr/bin/env python3
"""
Setup script for Meeting Scheduler Bot
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

def install_dependencies():
    """Install required dependencies."""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        sys.exit(1)

def setup_environment():
    """Set up environment configuration."""
    env_file = Path(".env")
    env_example = Path("../env.example")  # Use shared env.example from parent directory
    
    if env_file.exists():
        print("⚠️  .env file already exists, skipping creation")
        return
    
    if env_example.exists():
        try:
            with open(env_example, 'r') as src, open(env_file, 'w') as dst:
                dst.write(src.read())
            print("✅ Created .env file from shared template")
            print("📝 Please edit .env file with your actual API keys and configuration")
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
    else:
        print("❌ Shared env.example file not found in parent directory")

def check_google_credentials():
    """Check if Google credentials file exists."""
    credentials_file = Path("credentials.json")
    if credentials_file.exists():
        print("✅ Google credentials file found")
    else:
        print("⚠️  Google credentials file (credentials.json) not found")
        print("📝 Please download your OAuth 2.0 credentials from Google Cloud Console")
        print("   https://console.cloud.google.com/")

def main():
    """Main setup function."""
    print("🚀 Setting up Meeting Scheduler Bot...")
    print()
    
    check_python_version()
    install_dependencies()
    setup_environment()
    check_google_credentials()
    
    print()
    print("🎉 Setup complete!")
    print()
    print("Next steps:")
    print("1. Edit .env file with your API keys")
    print("2. Download Google OAuth credentials as 'credentials.json'")
    print("3. Run: python main.py")
    print()
    print("For detailed instructions, see README.md")

if __name__ == "__main__":
    main() 