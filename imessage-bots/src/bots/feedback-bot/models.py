from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

class FeedbackType(str, Enum):
    """Types of feedback that can be received."""
    FEATURE_REQUEST = "feature_request"
    BUG_REPORT = "bug_report"
    GENERAL_FEEDBACK = "general_feedback"
    QUESTION = "question"
    COMPLAINT = "complaint"
    PRAISE = "praise"
    USAGE_PATTERN = "usage_pattern"
    PAIN_POINT = "pain_point"

class ConversationState(str, Enum):
    """Conversation states for feedback collection."""
    INITIAL_CONTACT = "initial_contact"
    COLLECTING_FEEDBACK = "collecting_feedback"
    PROBING_DEEPER = "probing_deeper"
    CLARIFYING_DETAILS = "clarifying_details"
    SUMMARIZING = "summarizing"
    THANKING = "thanking"

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
    feedback_type: Optional[FeedbackType] = None
    extracted_insights: Optional[Dict] = None

class StructuredFeedback(BaseModel):
    """Model for structured feedback extraction."""
    feedback_type: FeedbackType
    summary: str
    raw_message: str
    context: Dict = Field(default_factory=dict)
    pain_points: List[str] = Field(default_factory=list)
    feature_requests: List[str] = Field(default_factory=list)
    current_solutions: List[str] = Field(default_factory=list)
    frequency: Optional[str] = None  # "daily", "weekly", "rarely"
    severity: Optional[str] = None  # "critical", "important", "nice-to-have"
    user_segment: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class CrossChatInsight(BaseModel):
    """Model for tracking insights that appear across multiple chats without revealing private info."""
    insight_id: str = Field(default_factory=lambda: str(datetime.now().timestamp()))
    feedback_type: FeedbackType
    theme: str  # General theme like "payment_issues", "navigation_confusion", etc.
    frequency_count: int = 1  # How many times this theme has appeared
    affected_chats: int = 1  # Number of different chats that mentioned this (not the specific GUIDs)
    first_seen: datetime = Field(default_factory=datetime.now)
    last_seen: datetime = Field(default_factory=datetime.now)
    suggested_probes: List[str] = Field(default_factory=list)  # Generic probes for this theme
    severity_level: str = "medium"  # low, medium, high based on frequency and feedback type

class UserProfile(BaseModel):
    """Model for tracking user information and patterns."""
    chat_guid: str
    first_contact: datetime = Field(default_factory=datetime.now)
    total_feedback_items: int = 0
    feedback_types: Dict[str, int] = Field(default_factory=dict)
    user_segment: Optional[str] = None
    engagement_level: str = "new"  # "new", "engaged", "power_user"
    preferred_communication_style: Optional[str] = None

class FeedbackConversation(BaseModel):
    """Model for tracking feedback conversation state and context."""
    chat_guid: str
    state: ConversationState = ConversationState.INITIAL_CONTACT
    conversation_history: List[ConversationMessage] = []
    current_feedback: Optional[StructuredFeedback] = None
    user_profile: UserProfile
    pending_probes: List[str] = Field(default_factory=list)  # Mom Test questions to ask
    cross_chat_probes_asked: List[str] = Field(default_factory=list)  # Cross-chat insights probes asked in this chat
    total_feedback_collected: int = 0
    total_questions_asked: int = 0  # Track total questions asked in this session
    last_interaction: datetime = Field(default_factory=datetime.now)
    awaiting_response: bool = False
    
    def add_user_message(self, content: str, feedback_type: Optional[FeedbackType] = None):
        """Add a user message to conversation history."""
        self.conversation_history.append(
            ConversationMessage(role="user", content=content, feedback_type=feedback_type)
        )
        self.last_interaction = datetime.now()
        self.awaiting_response = True
        # Keep only last 20 messages to avoid token limits
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
    
    def add_bot_message(self, content: str):
        """Add a bot message to conversation history."""
        self.conversation_history.append(
            ConversationMessage(role="assistant", content=content)
        )
        self.last_interaction = datetime.now()
        self.awaiting_response = False
        # Keep only last 20 messages to avoid token limits
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]

class FeedbackBotState(BaseModel):
    """Model for tracking the bot's global state across all chats."""
    total_conversations: int = 0
    total_feedback_items: int = 0
    feedback_by_type: Dict[str, int] = Field(default_factory=dict)
    cross_chat_insights: Dict[str, CrossChatInsight] = Field(default_factory=dict)  # Theme -> Insight
    active_chat_guids: List[str] = Field(default_factory=list)  # Currently monitored chats
    last_activity: Optional[datetime] = None 