from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

class ConversationState(str, Enum):
    """Enumeration of possible conversation states."""
    WAITING_FOR_COMMAND = "waiting_for_command"
    WAITING_FOR_EMAIL = "waiting_for_email"
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

class MeetingDetails(BaseModel):
    """Model for parsed meeting details from natural language."""
    title: str
    description: Optional[str] = None
    start_datetime: datetime
    end_datetime: datetime
    attendees: List[str] = []
    location: Optional[str] = None

class UserConversation(BaseModel):
    """Model for tracking user conversation state."""
    chat_guid: str
    state: ConversationState
    last_command: Optional[str] = None
    user_email: Optional[str] = None
    message_count: int = 0 