from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

class ConversationState(str, Enum):
    """Enumeration of possible conversation states for context-aware responses."""
    CASUAL_CHAT = "casual_chat"
    RESPONDING_TO_QUESTION = "responding_to_question"
    COMFORTING = "comforting"
    CELEBRATING = "celebrating"
    MISSING_YOU = "missing_you"
    PLANNING_TOGETHER = "planning_together"

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

class ConversationMessage(BaseModel):
    """Model for storing conversation history."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    sentiment: Optional[str] = None  # "positive", "negative", "neutral", "question"

class UserConversation(BaseModel):
    """Model for tracking user conversation state and context."""
    chat_guid: str
    state: ConversationState = ConversationState.CASUAL_CHAT
    conversation_history: List[ConversationMessage] = []
    last_user_message: Optional[str] = None
    last_user_message_time: Optional[datetime] = None
    last_bot_message_time: Optional[datetime] = None
    total_messages_sent: int = 0
    message_count: int = 0
    user_mood: Optional[str] = None  # "happy", "sad", "excited", "stressed", etc.
    awaiting_response: bool = False
    
    def add_user_message(self, content: str, sentiment: Optional[str] = None):
        """Add a user message to conversation history."""
        self.conversation_history.append(
            ConversationMessage(role="user", content=content, sentiment=sentiment)
        )
        self.last_user_message = content
        self.last_user_message_time = datetime.now()
        self.message_count += 1
        self.awaiting_response = True
        # Keep only last 20 messages to avoid token limits
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
    
    def add_bot_message(self, content: str):
        """Add a bot message to conversation history."""
        self.conversation_history.append(
            ConversationMessage(role="assistant", content=content)
        )
        self.last_bot_message_time = datetime.now()
        self.total_messages_sent += 1
        self.awaiting_response = False
        # Keep only last 20 messages to avoid token limits
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]

class LoverBotState(BaseModel):
    """Model for tracking the bot's global state."""
    total_conversations: int = 0
    total_messages_sent: int = 0
    last_activity: Optional[datetime] = None 