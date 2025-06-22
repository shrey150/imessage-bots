from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
import re
from models import UserConversation, ConversationState, LoverBotState

class ConversationManager:
    """Manages conversation state and context for reactive messaging."""
    
    def __init__(self):
        # In-memory storage for conversation states
        # Key: chat_guid, Value: UserConversation
        self._conversations: Dict[str, UserConversation] = {}
        self._global_state = LoverBotState()
    
    def get_conversation(self, chat_guid: str) -> Optional[UserConversation]:
        """Get conversation state for a chat."""
        return self._conversations.get(chat_guid)
    
    def start_conversation(self, chat_guid: str) -> UserConversation:
        """Start a new conversation or get existing one."""
        if chat_guid in self._conversations:
            conversation = self._conversations[chat_guid]
            conversation.message_count += 1
            return conversation
        
        # Create new conversation
        conversation = UserConversation(
            chat_guid=chat_guid,
            state=ConversationState.CASUAL_CHAT,
            message_count=1
        )
        self._conversations[chat_guid] = conversation
        self._global_state.total_conversations += 1
        return conversation
    
    def update_conversation(self, chat_guid: str, **kwargs) -> Optional[UserConversation]:
        """Update conversation state."""
        if chat_guid not in self._conversations:
            return None
        
        conversation = self._conversations[chat_guid]
        for key, value in kwargs.items():
            if hasattr(conversation, key):
                setattr(conversation, key, value)
        
        self._global_state.last_activity = datetime.now()
        return conversation
    
    def analyze_message_sentiment(self, message: str) -> Tuple[str, ConversationState]:
        """Analyze message sentiment and determine conversation state."""
        message_lower = message.lower()
        
        # Question patterns
        question_words = ['what', 'why', 'how', 'when', 'where', 'who', 'which', 'can', 'could', 'would', 'should', 'do', 'did', 'does', '?']
        if any(word in message_lower for word in question_words) or message.endswith('?'):
            return "question", ConversationState.RESPONDING_TO_QUESTION
        
        # Negative/sad patterns
        sad_words = ['sad', 'depressed', 'upset', 'angry', 'mad', 'frustrated', 'stressed', 'worried', 'anxious', 'tired', 'exhausted', 'bad day', 'terrible', 'awful', 'hate', 'cry', 'crying']
        if any(word in message_lower for word in sad_words):
            return "negative", ConversationState.COMFORTING
        
        # Positive/happy patterns
        happy_words = ['happy', 'excited', 'great', 'awesome', 'amazing', 'fantastic', 'wonderful', 'good news', 'celebration', 'party', 'love', 'promotion', 'success', 'accomplished', 'proud']
        if any(word in message_lower for word in happy_words):
            return "positive", ConversationState.CELEBRATING
        
        # Planning/future patterns
        planning_words = ['plan', 'planning', 'tomorrow', 'weekend', 'vacation', 'trip', 'date', 'dinner', 'movie', 'visit', 'meet', 'together', 'let\'s', 'should we', 'want to']
        if any(word in message_lower for word in planning_words):
            return "planning", ConversationState.PLANNING_TOGETHER
        
        # Miss you patterns
        missing_words = ['miss', 'missing', 'wish you', 'can\'t wait', 'see you', 'when will', 'lonely', 'alone']
        if any(word in message_lower for word in missing_words):
            return "missing", ConversationState.MISSING_YOU
        
        return "neutral", ConversationState.CASUAL_CHAT
    
    def process_user_message(self, chat_guid: str, message: str) -> UserConversation:
        """Process a user message and update conversation context."""
        # Get or create conversation
        conversation = self.start_conversation(chat_guid)
        
        # Analyze sentiment and determine state
        sentiment, suggested_state = self.analyze_message_sentiment(message)
        
        # Update conversation with message and context
        conversation.add_user_message(message, sentiment)
        conversation.state = suggested_state
        
        # Determine user mood based on recent messages
        recent_sentiments = [msg.sentiment for msg in conversation.conversation_history[-3:] if msg.role == "user" and msg.sentiment]
        if recent_sentiments:
            if recent_sentiments.count("negative") >= 2:
                conversation.user_mood = "sad"
            elif recent_sentiments.count("positive") >= 2:
                conversation.user_mood = "happy"
            elif recent_sentiments.count("question") >= 2:
                conversation.user_mood = "curious"
            else:
                conversation.user_mood = "neutral"
        
        return conversation
    
    def should_send_proactive_message(self, chat_guid: str, interval_minutes: int) -> bool:
        """Determine if it's time to send a proactive message."""
        conversation = self.get_conversation(chat_guid)
        if not conversation:
            return True  # No conversation exists, send first message
        
        # Don't send if user is awaiting a response
        if conversation.awaiting_response:
            return False
        
        # Check time since last bot message
        if not conversation.last_bot_message_time:
            return True
        
        time_since_last = datetime.now() - conversation.last_bot_message_time
        return time_since_last >= timedelta(minutes=interval_minutes)
    
    def get_conversation_context(self, chat_guid: str) -> Dict:
        """Get comprehensive conversation context for AI generation."""
        conversation = self.get_conversation(chat_guid)
        if not conversation:
            return {"context": "new_conversation", "state": ConversationState.CASUAL_CHAT}
        
        recent_messages = conversation.conversation_history[-5:] if conversation.conversation_history else []
        
        return {
            "state": conversation.state,
            "user_mood": conversation.user_mood,
            "last_user_message": conversation.last_user_message,
            "awaiting_response": conversation.awaiting_response,
            "message_count": conversation.message_count,
            "recent_messages": [{"role": msg.role, "content": msg.content[:100], "sentiment": msg.sentiment} for msg in recent_messages],
            "time_since_last_user_message": (datetime.now() - conversation.last_user_message_time).total_seconds() / 60 if conversation.last_user_message_time else None
        }
    
    def mark_message_sent(self, chat_guid: str, message: str):
        """Mark that a message was sent."""
        conversation = self.get_conversation(chat_guid)
        if conversation:
            conversation.add_bot_message(message)
        
        self._global_state.total_messages_sent += 1
        self._global_state.last_activity = datetime.now()
    
    def clear_conversation(self, chat_guid: str) -> None:
        """Clear conversation state for a chat."""
        if chat_guid in self._conversations:
            del self._conversations[chat_guid]
    
    def get_stats(self) -> Dict:
        """Get conversation statistics."""
        active_conversations = len(self._conversations)
        awaiting_responses = len([c for c in self._conversations.values() if c.awaiting_response])
        
        state_counts = {}
        for state in ConversationState:
            state_counts[state.value] = len([c for c in self._conversations.values() if c.state == state])
        
        return {
            "total_conversations": self._global_state.total_conversations,
            "active_conversations": active_conversations,
            "awaiting_responses": awaiting_responses,
            "total_messages_sent": self._global_state.total_messages_sent,
            "last_activity": self._global_state.last_activity.isoformat() if self._global_state.last_activity else None,
            "conversation_states": state_counts
        }

# Global conversation manager instance
conversation_manager = ConversationManager() 