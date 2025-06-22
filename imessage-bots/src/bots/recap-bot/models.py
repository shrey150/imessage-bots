"""Data models for the recap bot."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from enum import Enum

class WebhookData(BaseModel):
    """Model for incoming webhook data from BlueBubbles."""
    type: str
    data: Dict[str, Any]

class MessageData(BaseModel):
    """Model for message data."""
    guid: str
    text: Optional[str] = None
    handle: Optional[Dict[str, Any]] = None
    chat: Optional[Dict[str, Any]] = None
    dateCreated: Optional[int] = None
    isFromMe: Optional[bool] = None

class ChatState(BaseModel):
    """Model for tracking chat state and unread messages."""
    chat_guid: str
    last_read_message_guid: Optional[str] = None
    last_read_timestamp: Optional[int] = None
    unread_count: int = 0
    total_messages_seen: int = 0
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

class MessageSummary(BaseModel):
    """Model for message summary data."""
    sender: str
    timestamp: datetime
    content: str
    is_from_user: bool = False

class RecapResponse(BaseModel):
    """Model for recap response."""
    chat_guid: str
    unread_count: int
    messages_analyzed: int
    summary: str
    key_points: List[str]
    participants: List[str]
    time_range: str 