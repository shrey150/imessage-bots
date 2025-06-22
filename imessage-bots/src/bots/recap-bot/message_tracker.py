"""Message tracking and state management for the recap bot."""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from models import ChatState, MessageSummary
import logging

logger = logging.getLogger(__name__)

class MessageTracker:
    """Manages message tracking and unread counts for chats."""
    
    def __init__(self, storage_file: str = "chat_states.json"):
        """
        Initialize the message tracker.
        
        Args:
            storage_file: Path to the JSON file for storing chat states
        """
        self.storage_file = storage_file
        self.chat_states: Dict[str, ChatState] = {}
        self.load_states()
    
    def load_states(self):
        """Load chat states from storage file."""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    for chat_guid, state_data in data.items():
                        # Convert datetime strings back to datetime objects
                        if 'created_at' in state_data:
                            state_data['created_at'] = datetime.fromisoformat(state_data['created_at'])
                        if 'updated_at' in state_data:
                            state_data['updated_at'] = datetime.fromisoformat(state_data['updated_at'])
                        self.chat_states[chat_guid] = ChatState(**state_data)
                logger.info(f"Loaded {len(self.chat_states)} chat states from storage")
        except Exception as e:
            logger.error(f"Error loading chat states: {e}")
            self.chat_states = {}
    
    def save_states(self):
        """Save chat states to storage file."""
        try:
            data = {}
            for chat_guid, state in self.chat_states.items():
                state_dict = state.dict()
                # Convert datetime objects to strings for JSON serialization
                state_dict['created_at'] = state.created_at.isoformat()
                state_dict['updated_at'] = state.updated_at.isoformat()
                data[chat_guid] = state_dict
            
            with open(self.storage_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved {len(self.chat_states)} chat states to storage")
        except Exception as e:
            logger.error(f"Error saving chat states: {e}")
    
    def get_chat_state(self, chat_guid: str) -> ChatState:
        """
        Get or create chat state for a given chat.
        
        Args:
            chat_guid: The GUID of the chat
            
        Returns:
            ChatState object for the chat
        """
        if chat_guid not in self.chat_states:
            self.chat_states[chat_guid] = ChatState(chat_guid=chat_guid)
            self.save_states()
        return self.chat_states[chat_guid]
    
    def update_message_count(self, chat_guid: str, message_guid: str, timestamp: int):
        """
        Update the message count for a chat.
        
        Args:
            chat_guid: The GUID of the chat
            message_guid: The GUID of the message
            timestamp: The timestamp of the message
        """
        state = self.get_chat_state(chat_guid)
        state.total_messages_seen += 1
        state.unread_count += 1
        state.updated_at = datetime.now()
        self.save_states()
        logger.debug(f"Updated message count for {chat_guid}: {state.unread_count} unread")
    
    def mark_as_read(self, chat_guid: str, message_guid: str, timestamp: int):
        """
        Mark messages as read up to a specific message.
        
        Args:
            chat_guid: The GUID of the chat
            message_guid: The GUID of the last read message
            timestamp: The timestamp of the last read message
        """
        state = self.get_chat_state(chat_guid)
        state.last_read_message_guid = message_guid
        state.last_read_timestamp = timestamp
        state.unread_count = 0  # Reset unread count
        state.updated_at = datetime.now()
        self.save_states()
        logger.info(f"Marked {chat_guid} as read up to message {message_guid}")
    
    def get_unread_count(self, chat_guid: str) -> int:
        """
        Get the number of unread messages for a chat.
        
        Args:
            chat_guid: The GUID of the chat
            
        Returns:
            Number of unread messages
        """
        state = self.get_chat_state(chat_guid)
        return state.unread_count
    
    def get_last_read_timestamp(self, chat_guid: str) -> Optional[int]:
        """
        Get the timestamp of the last read message.
        
        Args:
            chat_guid: The GUID of the chat
            
        Returns:
            Timestamp of last read message, or None if no messages read
        """
        state = self.get_chat_state(chat_guid)
        return state.last_read_timestamp
    
    def get_stats(self) -> Dict[str, any]:
        """Get statistics about tracked chats."""
        total_chats = len(self.chat_states)
        total_unread = sum(state.unread_count for state in self.chat_states.values())
        active_chats = sum(1 for state in self.chat_states.values() if state.unread_count > 0)
        
        return {
            "total_chats": total_chats,
            "active_chats": active_chats,
            "total_unread_messages": total_unread,
            "average_unread_per_chat": total_unread / total_chats if total_chats > 0 else 0
        } 