import os
from typing import Optional, List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Configuration settings for the Feedback bot."""
    
    # BlueBubbles Server Configuration
    BLUEBUBBLES_SERVER_URL: str = os.getenv("BLUEBUBBLES_SERVER_URL", "http://localhost:1234")
    BLUEBUBBLES_PASSWORD: str = os.getenv("BLUEBUBBLES_PASSWORD", "your-server-password")
    
    # FastAPI Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8081"))  # Different port from other bots
    
    # Feedback Bot Configuration
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Multiple Chat GUIDs - can be comma-separated list
    _CHAT_GUIDS_STR: str = os.getenv("CHAT_GUIDS", os.getenv("CHAT_GUID", ""))  # Support both CHAT_GUIDS and legacy CHAT_GUID
    CHAT_GUIDS: List[str] = [guid.strip() for guid in _CHAT_GUIDS_STR.split(",") if guid.strip()] if _CHAT_GUIDS_STR else []
    
    # Legacy single chat GUID support (deprecated but maintained for backwards compatibility)
    CHAT_GUID: str = CHAT_GUIDS[0] if CHAT_GUIDS else ""
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Linear API Configuration
    LINEAR_API_KEY: str = os.getenv("LINEAR_API_KEY", "")
    LINEAR_TEAM_KEY: Optional[str] = os.getenv("LINEAR_TEAM_KEY")  # Optional team key (e.g., "PRODUCT")
    ENABLE_LINEAR_INTEGRATION: bool = os.getenv("ENABLE_LINEAR_INTEGRATION", "true").lower() == "true"
    
    # Auto-triaging settings
    AUTO_TRIAGE_ON_SESSION_END: bool = os.getenv("AUTO_TRIAGE_ON_SESSION_END", "true").lower() == "true"
    NOTIFY_USER_ON_TRIAGE: bool = os.getenv("NOTIFY_USER_ON_TRIAGE", "false").lower() == "true"
    
    # Bot Configuration
    FOUNDER_NAME: str = os.getenv("FOUNDER_NAME", "founder")  # What the bot calls the founder
    PRODUCT_NAME: str = os.getenv("PRODUCT_NAME", "your product")  # Name of the product being tested
    
    # Feedback Collection Settings
    MAX_QUESTIONS_PER_SESSION: int = int(os.getenv("MAX_QUESTIONS_PER_SESSION", "3"))  # Max total questions per session
    AUTO_SUMMARIZE_THRESHOLD: int = int(os.getenv("AUTO_SUMMARIZE_THRESHOLD", "3"))  # Auto-summarize after N questions
    
    # Cross-chat insights settings
    ENABLE_CROSS_CHAT_INSIGHTS: bool = os.getenv("ENABLE_CROSS_CHAT_INSIGHTS", "true").lower() == "true"
    CROSS_CHAT_PROBE_FREQUENCY: float = float(os.getenv("CROSS_CHAT_PROBE_FREQUENCY", "0.3"))  # 30% chance to ask cross-chat probe
    
    @classmethod
    def validate(cls) -> None:
        """Validate that all required configuration is present."""
        if not cls.BLUEBUBBLES_PASSWORD or cls.BLUEBUBBLES_PASSWORD == "your-server-password":
            raise ValueError("BLUEBUBBLES_PASSWORD environment variable must be set to your actual password")
        if not cls.CHAT_GUIDS:
            raise ValueError("CHAT_GUIDS environment variable is required - provide comma-separated chat GUIDs where the bot will receive feedback")
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required for GPT-4o")
        
        # Linear validation (only if Linear integration is enabled)
        if cls.ENABLE_LINEAR_INTEGRATION and not cls.LINEAR_API_KEY:
            raise ValueError("LINEAR_API_KEY environment variable is required when ENABLE_LINEAR_INTEGRATION is true")
    
    @classmethod
    def is_monitored_chat(cls, chat_guid: str) -> bool:
        """Check if a chat GUID is in our monitored list."""
        return chat_guid in cls.CHAT_GUIDS

config = Config() 