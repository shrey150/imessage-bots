from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from models import Message

logger = logging.getLogger(__name__)

class ChatHistory:
    """Track recent messages for each chat to provide context for Gork responses."""
    
    def __init__(self):
        # Dictionary to store recent messages for each chat
        # Format: {chat_guid: [(message_text, message_guid, timestamp), ...]}
        self._chat_messages: Dict[str, List[Tuple[str, str, datetime]]] = {}
        self._max_messages_per_chat = 10  # Keep last 10 messages
        self._message_ttl_hours = 24  # Keep messages for 24 hours
    
    def add_message(self, chat_guid: str, message_text: str, message_guid: str, timestamp: Optional[datetime] = None) -> None:
        """Add a new message to the chat history."""
        if timestamp is None:
            timestamp = datetime.now()
        
        if chat_guid not in self._chat_messages:
            self._chat_messages[chat_guid] = []
        
        # Add the new message
        self._chat_messages[chat_guid].append((message_text, message_guid, timestamp))
        
        # Clean up old messages
        self._cleanup_chat_history(chat_guid)
    
    def get_previous_message(self, chat_guid: str) -> Optional[Tuple[str, str]]:
        """Get the most recent message before the current one."""
        if chat_guid not in self._chat_messages or len(self._chat_messages[chat_guid]) < 2:
            return None
        
        # Return the second-to-last message (previous message) as (text, guid)
        prev_msg = self._chat_messages[chat_guid][-2]
        return (prev_msg[0], prev_msg[1])
    
    def get_recent_messages(self, chat_guid: str, count: int = 5) -> List[str]:
        """Get the most recent messages from a chat (excluding the current trigger message)."""
        if chat_guid not in self._chat_messages:
            return []
        
        messages = self._chat_messages[chat_guid]
        # Return up to 'count' messages, excluding the most recent one (which is the trigger)
        return [msg[0] for msg in messages[:-1][-count:]]
    
    def _cleanup_chat_history(self, chat_guid: str) -> None:
        """Remove old messages to keep memory usage reasonable."""
        if chat_guid not in self._chat_messages:
            return
        
        messages = self._chat_messages[chat_guid]
        current_time = datetime.now()
        
        # Remove messages older than TTL
        messages = [
            (text, msg_guid, timestamp) for text, msg_guid, timestamp in messages
            if current_time - timestamp < timedelta(hours=self._message_ttl_hours)
        ]
        
        # Keep only the most recent messages
        if len(messages) > self._max_messages_per_chat:
            messages = messages[-self._max_messages_per_chat:]
        
        self._chat_messages[chat_guid] = messages
    
    def get_stats(self) -> Dict[str, int]:
        """Get statistics about tracked messages."""
        total_messages = sum(len(messages) for messages in self._chat_messages.values())
        return {
            "total_chats": len(self._chat_messages),
            "total_messages": total_messages
        }

# Global instance
chat_history = ChatHistory() 