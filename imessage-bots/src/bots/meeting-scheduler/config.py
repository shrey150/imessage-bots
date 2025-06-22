import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration settings for the meeting scheduler bot."""
    
    # BlueBubbles Server Configuration
    BLUEBUBBLES_SERVER_URL: str = os.getenv("BLUEBUBBLES_SERVER_URL", "http://localhost:1234")
    BLUEBUBBLES_PASSWORD: str = os.getenv("BLUEBUBBLES_PASSWORD", "your-server-password")
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = "gpt-4o"
    
    # Google Calendar Configuration
    GOOGLE_CREDENTIALS_FILE: str = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
    GOOGLE_TOKEN_FILE: str = os.getenv("GOOGLE_TOKEN_FILE", "token.json")
    GOOGLE_CALENDAR_ID: str = os.getenv("GOOGLE_CALENDAR_ID", "primary")
    
    # FastAPI Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT") or "8001")
    
    # Bot Configuration
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    TRIGGER_PHRASE: str = "!schedule"
    
    @classmethod
    def validate(cls) -> None:
        """Validate that all required configuration is present."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        if not cls.BLUEBUBBLES_PASSWORD or cls.BLUEBUBBLES_PASSWORD == "your-server-password":
            raise ValueError("BLUEBUBBLES_PASSWORD environment variable must be set to your actual password")
        if not os.path.exists(cls.GOOGLE_CREDENTIALS_FILE):
            raise ValueError(f"Google credentials file not found: {cls.GOOGLE_CREDENTIALS_FILE}")

config = Config() 