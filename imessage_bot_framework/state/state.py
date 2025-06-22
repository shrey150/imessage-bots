"""Simple state management for bots."""

import json
import os
from typing import Any, Optional, Dict
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)


class State:
    """Simple persistent key-value store for bot state."""
    
    def __init__(self, storage_file: str = "bot_state.json"):
        """
        Initialize the state manager.
        
        Args:
            storage_file: Path to the JSON file for storing state
        """
        self.storage_file = storage_file
        self._state: Dict[str, Any] = {}
        self._conversations: Dict[str, Dict[str, Any]] = {}
        self.load()
    
    def load(self):
        """Load state from storage file."""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    self._state = data.get('state', {})
                    self._conversations = data.get('conversations', {})
                logger.info(f"Loaded state from {self.storage_file}")
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            self._state = {}
            self._conversations = {}
    
    def save(self):
        """Save state to storage file."""
        try:
            data = {
                'state': self._state,
                'conversations': self._conversations
            }
            with open(self.storage_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved state to {self.storage_file}")
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from state.
        
        Args:
            key: The state key
            default: Default value if key doesn't exist
            
        Returns:
            The stored value or default
        """
        return self._state.get(key, default)
    
    def set(self, key: str, value: Any):
        """
        Set a value in state.
        
        Args:
            key: The state key
            value: The value to store
        """
        self._state[key] = value
        self.save()
    
    def delete(self, key: str):
        """
        Delete a key from state.
        
        Args:
            key: The state key to delete
        """
        if key in self._state:
            del self._state[key]
            self.save()
    
    def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment a numeric value in state.
        
        Args:
            key: The state key
            amount: Amount to increment by
            
        Returns:
            The new value
        """
        current = self.get(key, 0)
        new_value = current + amount
        self.set(key, new_value)
        return new_value
    
    def append(self, key: str, value: Any):
        """
        Append to a list in state.
        
        Args:
            key: The state key
            value: Value to append
        """
        current = self.get(key, [])
        if not isinstance(current, list):
            current = [current]
        current.append(value)
        self.set(key, current)
    
    @contextmanager
    def conversation(self, user_id: str):
        """
        Context manager for handling conversations.
        
        Args:
            user_id: The user identifier
            
        Yields:
            ConversationContext object
        """
        if user_id not in self._conversations:
            self._conversations[user_id] = {}
        
        context = ConversationContext(user_id, self._conversations[user_id], self)
        try:
            yield context
        finally:
            self.save()
    
    def clear_conversation(self, user_id: str):
        """
        Clear conversation state for a user.
        
        Args:
            user_id: The user identifier
        """
        if user_id in self._conversations:
            del self._conversations[user_id]
            self.save()
    
    def get_all_keys(self) -> list:
        """Get all state keys."""
        return list(self._state.keys())
    
    def clear_all(self):
        """Clear all state."""
        self._state = {}
        self._conversations = {}
        self.save()


class ConversationContext:
    """Context for managing conversation state."""
    
    def __init__(self, user_id: str, conversation_data: Dict[str, Any], state_manager: State):
        """
        Initialize conversation context.
        
        Args:
            user_id: The user identifier
            conversation_data: The conversation data dictionary
            state_manager: The state manager instance
        """
        self.user_id = user_id
        self._data = conversation_data
        self._state_manager = state_manager
    
    def ask(self, question: str) -> str:
        """
        Ask a question and wait for response (placeholder).
        
        Args:
            question: The question to ask
            
        Returns:
            The user's response (would need actual implementation)
        """
        # This would need integration with the bot's message handling
        # For now, just store the question
        self._data['last_question'] = question
        return ""
    
    def set(self, key: str, value: Any):
        """
        Set a value in conversation context.
        
        Args:
            key: The key
            value: The value
        """
        self._data[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from conversation context.
        
        Args:
            key: The key
            default: Default value
            
        Returns:
            The stored value or default
        """
        return self._data.get(key, default)
    
    def save(self, data: Dict[str, Any]):
        """
        Save data to conversation context.
        
        Args:
            data: Dictionary of data to save
        """
        self._data.update(data)
    
    def clear(self):
        """Clear conversation context."""
        self._data.clear()
    
    def is_complete(self) -> bool:
        """Check if conversation is complete."""
        return self._data.get('complete', False)
    
    def mark_complete(self):
        """Mark conversation as complete."""
        self._data['complete'] = True 