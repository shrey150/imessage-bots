"""Configuration settings for the recap bot."""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot Configuration
TRIGGER_PHRASE = os.getenv("RECAP_TRIGGER_PHRASE", "!recap")
BOT_NAME = "Recap Bot"
BOT_VERSION = "1.0.0"

# Server Configuration
HOST = os.getenv("RECAP_HOST", "127.0.0.1")
PORT = int(os.getenv("RECAP_PORT", "8002"))  # Different port from other bots

# BlueBubbles Configuration
BLUEBUBBLES_SERVER_URL = os.getenv("BLUEBUBBLES_SERVER_URL", "http://localhost:1234")
BLUEBUBBLES_PASSWORD = os.getenv("BLUEBUBBLES_PASSWORD", "")

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# Note: We rely on BlueBubbles' isFromMe flag to identify your messages
# YOUR_PHONE_NUMBER is no longer needed

# Recap Configuration
MAX_MESSAGES_TO_ANALYZE = int(os.getenv("MAX_MESSAGES_TO_ANALYZE", "200"))
MAX_SUMMARY_LENGTH = int(os.getenv("MAX_SUMMARY_LENGTH", "500"))

# Validation
def validate_config():
    """Validate that all required configuration is present."""
    missing_vars = []
    
    if not BLUEBUBBLES_SERVER_URL:
        missing_vars.append("BLUEBUBBLES_SERVER_URL")
    
    if not BLUEBUBBLES_PASSWORD:
        missing_vars.append("BLUEBUBBLES_PASSWORD")
    
    if not OPENAI_API_KEY:
        missing_vars.append("OPENAI_API_KEY")
    
    # YOUR_PHONE_NUMBER no longer required - we use isFromMe flag
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

if __name__ == "__main__":
    validate_config()
    print("✅ Configuration is valid!") 