from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from enum import Enum

class ConversationState(str, Enum):
    """Enumeration of possible conversation states."""
    WAITING_FOR_LINKEDIN = "waiting_for_linkedin"
    PROCESSING = "processing"

class Chat(BaseModel):
    """Model for chat information in BlueBubbles webhook."""
    guid: str
    chat_identifier: Optional[str] = None
    display_name: Optional[str] = None

class Message(BaseModel):
    """Model for message data in BlueBubbles webhook."""
    guid: str
    text: Optional[str] = None
    isFromMe: bool = Field(alias="isFromMe")
    chats: List[Chat] = []
    dateCreated: Optional[int] = Field(alias="dateCreated", default=None)
    
    class Config:
        populate_by_name = True

class WebhookData(BaseModel):
    """Model for the main webhook payload from BlueBubbles."""
    type: str
    data: Optional[Message] = None

class LinkedInProfile(BaseModel):
    """Model for scraped LinkedIn profile data."""
    name: Optional[str] = None
    headline: Optional[str] = None
    current_position: Optional[str] = None
    location: Optional[str] = None
    about: Optional[str] = None
    experience: List[Dict[str, Any]] = []
    education: List[Dict[str, Any]] = []
    skills: List[str] = []
    connections: Optional[str] = None
    profile_url: Optional[str] = None
    raw_text: str = ""

class UserConversation(BaseModel):
    """Model for tracking user conversation state."""
    chat_guid: str
    state: ConversationState
    linkedin_url: Optional[str] = None
    profile_data: Optional[LinkedInProfile] = None
    message_count: int = 0 