from typing import Dict, Optional
from models import UserConversation, ConversationState

class ConversationManager:
    """Manages conversation state for multiple users."""
    
    def __init__(self):
        # In-memory storage for conversation states
        # Key: chat_guid, Value: UserConversation
        self._conversations: Dict[str, UserConversation] = {}
    
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
            state=ConversationState.WAITING_FOR_LINKEDIN,
            message_count=1
        )
        self._conversations[chat_guid] = conversation
        return conversation
    
    def update_conversation(self, chat_guid: str, **kwargs) -> Optional[UserConversation]:
        """Update conversation state."""
        if chat_guid not in self._conversations:
            return None
        
        conversation = self._conversations[chat_guid]
        for key, value in kwargs.items():
            if hasattr(conversation, key):
                setattr(conversation, key, value)
        
        return conversation
    
    def clear_conversation(self, chat_guid: str) -> None:
        """Clear conversation state for a chat."""
        if chat_guid in self._conversations:
            del self._conversations[chat_guid]
    
    def get_stats(self) -> Dict:
        """Get conversation statistics."""
        return {
            "total_conversations": len(self._conversations),
            "waiting_for_linkedin": len([c for c in self._conversations.values() if c.state == ConversationState.WAITING_FOR_LINKEDIN]),
            "processing": len([c for c in self._conversations.values() if c.state == ConversationState.PROCESSING])
        }

# Global conversation manager instance
conversation_manager = ConversationManager() 