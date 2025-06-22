import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration settings for the Lover bot."""
    
    # BlueBubbles Server Configuration
    BLUEBUBBLES_SERVER_URL: str = os.getenv("BLUEBUBBLES_SERVER_URL", "http://localhost:1234")
    BLUEBUBBLES_PASSWORD: str = os.getenv("BLUEBUBBLES_PASSWORD", "your-server-password")
    
    # FastAPI Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8080"))  # Different port from other bots
    
    # Lover Bot Configuration
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    CHAT_GUID: str = os.getenv("CHAT_GUID", "")  # The chat where the bot will send messages
    MESSAGE_INTERVAL_MINUTES: int = int(os.getenv("MESSAGE_INTERVAL_MINUTES", "10"))  # Send message every 10 minutes
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Bot Personality Configuration
    LOVER_NAME: str = os.getenv("LOVER_NAME", "Alex")  # Your AI lover's name
    USER_NAME: str = os.getenv("USER_NAME", "babe")    # What your AI lover calls you
    
    @classmethod
    def validate(cls) -> None:
        """Validate that all required configuration is present."""
        if not cls.BLUEBUBBLES_PASSWORD or cls.BLUEBUBBLES_PASSWORD == "your-server-password":
            raise ValueError("BLUEBUBBLES_PASSWORD environment variable must be set to your actual password")
        if not cls.CHAT_GUID:
            raise ValueError("CHAT_GUID environment variable is required - this is where the bot will send messages")
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required for GPT-4o")

config = Config() 