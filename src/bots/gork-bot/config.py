import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration settings for the gork bot."""
    
    # BlueBubbles Server Configuration
    BLUEBUBBLES_SERVER_URL: str = os.getenv("BLUEBUBBLES_SERVER_URL", "http://localhost:1234")
    BLUEBUBBLES_PASSWORD: str = os.getenv("BLUEBUBBLES_PASSWORD", "your-server-password")
    
    # Chat Configuration
    CHAT_GUID: str = os.getenv("CHAT_GUID", "")
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = "gpt-4o"
    
    # FastAPI Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT") or "8002")
    
    # Bot Configuration
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    TRIGGER_PHRASE: str = "@gork"
    
    @classmethod
    def validate(cls) -> None:
        """Validate that all required configuration is present."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        if not cls.BLUEBUBBLES_PASSWORD or cls.BLUEBUBBLES_PASSWORD == "your-server-password":
            raise ValueError("BLUEBUBBLES_PASSWORD environment variable must be set to your actual password")
        if not cls.CHAT_GUID:
            raise ValueError("CHAT_GUID environment variable is required")

config = Config() 