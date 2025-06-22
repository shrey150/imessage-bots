"""Message class for handling incoming iMessages."""

import requests
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class Message:
    """Represents an incoming iMessage with methods to respond."""
    
    def __init__(self, text: str, sender: str, chat_guid: str, raw_data: Dict[str, Any], bot_config: Dict[str, Any]):
        """
        Initialize a Message object.
        
        Args:
            text: The message text content
            sender: The sender's identifier
            chat_guid: The chat GUID where message was sent
            raw_data: Raw webhook data from BlueBubbles
            bot_config: Bot configuration (BlueBubbles URL, password, etc.)
        """
        self.text = text or ""
        self.sender = sender
        self.chat_guid = chat_guid
        self.is_from_me = raw_data.get('isFromMe', False)
        self.timestamp = datetime.fromtimestamp(raw_data.get('dateCreated', 0) / 1000) if raw_data.get('dateCreated') else datetime.now()
        self.guid = raw_data.get('guid', '')
        self._raw = raw_data
        self._bot_config = bot_config
        
    def reply(self, text: str) -> bool:
        """
        Reply to this message in the same chat.
        
        Args:
            text: The reply text
            
        Returns:
            True if message sent successfully, False otherwise
        """
        return self.send_to_chat(text, self.chat_guid)
        
    def send_to_chat(self, text: str, chat_guid: Optional[str] = None) -> bool:
        """
        Send a message to any chat.
        
        Args:
            text: The message text
            chat_guid: The chat GUID to send to (defaults to current chat)
            
        Returns:
            True if message sent successfully, False otherwise
        """
        target_chat = chat_guid or self.chat_guid
        
        try:
            params = {"password": self._bot_config.get("bluebubbles_password")}
            data = {
                "chatGuid": target_chat,
                "tempGuid": str(uuid.uuid4()),
                "message": text,
                "method": "apple-script",
                "subject": "",
                "effectId": "",
                "selectedMessageGuid": ""
            }
            
            url = f"{self._bot_config.get('bluebubbles_url')}/api/v1/message/text"
            
            response = requests.post(
                url,
                json=data,
                params=params,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            response.raise_for_status()
            logger.info(f"Successfully sent message to {target_chat}")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Failed to send message to BlueBubbles: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending message: {e}")
            return False
    
    @property
    def chat(self):
        """Get a Chat object for this message's chat."""
        from .chat import Chat
        return Chat(self.chat_guid, self._bot_config)
    
    def __str__(self) -> str:
        return f"Message(text='{self.text[:50]}...', sender='{self.sender}', chat='{self.chat_guid}')"
    
    def __repr__(self) -> str:
        return self.__str__() 