import logging
from typing import Dict, Optional
from models import UserConversation, ConversationState

logger = logging.getLogger(__name__)

class ConversationManager:
    """Manages conversation state for multiple users."""
    
    def __init__(self):
        self.conversations: Dict[str, UserConversation] = {}
    
    def start_conversation(self, chat_guid: str) -> UserConversation:
        """Start or get existing conversation for a chat."""
        if chat_guid not in self.conversations:
            self.conversations[chat_guid] = UserConversation(
                chat_guid=chat_guid,
                state=ConversationState.WAITING_FOR_COMMAND,
                message_count=0
            )
            logger.info(f"Started new conversation for chat: {chat_guid}")
        
        # Increment message count
        self.conversations[chat_guid].message_count += 1
        return self.conversations[chat_guid]
    
    def update_conversation(
        self, 
        chat_guid: str, 
        state: Optional[ConversationState] = None,
        last_command: Optional[str] = None,
        user_email: Optional[str] = None
    ) -> UserConversation:
        """Update conversation state."""
        if chat_guid not in self.conversations:
            self.start_conversation(chat_guid)
        
        conversation = self.conversations[chat_guid]
        
        if state is not None:
            conversation.state = state
            logger.info(f"Updated conversation state for {chat_guid}: {state}")
        
        if last_command is not None:
            conversation.last_command = last_command
        
        if user_email is not None:
            conversation.user_email = user_email
        
        return conversation
    
    def get_conversation(self, chat_guid: str) -> Optional[UserConversation]:
        """Get conversation state for a chat."""
        return self.conversations.get(chat_guid)
    
    def reset_conversation(self, chat_guid: str) -> None:
        """Reset conversation state for a chat."""
        if chat_guid in self.conversations:
            del self.conversations[chat_guid]
            logger.info(f"Reset conversation for chat: {chat_guid}")
    
    def get_stats(self) -> Dict[str, int]:
        """Get conversation statistics."""
        return {
            "total_conversations": len(self.conversations),
            "active_conversations": len([
                c for c in self.conversations.values() 
                if c.state == ConversationState.PROCESSING
            ])
        }

# Global conversation manager instance
conversation_manager = ConversationManager() 