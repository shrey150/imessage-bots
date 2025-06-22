from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from datetime import datetime

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

class GorkResponse(BaseModel):
    """Model for storing Gork's sarcastic response."""
    original_message: str
    user_request: str
    sarcastic_explanation: str
    chat_guid: str
    timestamp: datetime 