"""Chat class for interacting with iMessage chats."""

import requests
import uuid
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class Chat:
    """Represents an iMessage chat with methods to interact with it."""
    
    def __init__(self, guid: str, bot_config: Dict[str, Any]):
        """
        Initialize a Chat object.
        
        Args:
            guid: The chat GUID
            bot_config: Bot configuration (BlueBubbles URL, password, etc.)
        """
        self.guid = guid
        self._bot_config = bot_config
        
    def send(self, text: str) -> bool:
        """
        Send a message to this chat.
        
        Args:
            text: The message text
            
        Returns:
            True if message sent successfully, False otherwise
        """
        try:
            params = {"password": self._bot_config.get("bluebubbles_password")}
            data = {
                "chatGuid": self.guid,
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
            logger.info(f"Successfully sent message to chat {self.guid}")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Failed to send message to BlueBubbles: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending message: {e}")
            return False
    
    def get_messages(self, limit: int = 50, since_timestamp: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get recent messages from this chat.
        
        Args:
            limit: Maximum number of messages to fetch
            since_timestamp: Only get messages after this timestamp
            
        Returns:
            List of message dictionaries
        """
        try:
            params = {
                "password": self._bot_config.get("bluebubbles_password"),
                "limit": limit,
                "sort": "DESC"  # Get newest messages first
            }
            
            if since_timestamp:
                params["after"] = since_timestamp
            
            url = f"{self._bot_config.get('bluebubbles_url')}/api/v1/chat/{self.guid}/message"
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            messages = data.get("data", [])
            
            logger.info(f"Retrieved {len(messages)} messages from chat {self.guid}")
            return messages
            
        except requests.RequestException as e:
            logger.error(f"Error fetching messages from BlueBubbles: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching messages: {e}")
            return []
    
    def get_participants(self) -> List[str]:
        """
        Get list of participants in this chat.
        
        Returns:
            List of participant identifiers
        """
        try:
            params = {"password": self._bot_config.get("bluebubbles_password")}
            url = f"{self._bot_config.get('bluebubbles_url')}/api/v1/chat/{self.guid}"
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            chat_data = data.get("data", {})
            participants = chat_data.get("participants", [])
            
            # Extract participant addresses/identifiers
            participant_list = []
            for participant in participants:
                if isinstance(participant, dict):
                    address = participant.get("address", "")
                    if address:
                        participant_list.append(address)
                elif isinstance(participant, str):
                    participant_list.append(participant)
            
            logger.info(f"Retrieved {len(participant_list)} participants from chat {self.guid}")
            return participant_list
            
        except requests.RequestException as e:
            logger.error(f"Error fetching chat participants: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching participants: {e}")
            return []
    
    def __str__(self) -> str:
        return f"Chat(guid='{self.guid}')"
    
    def __repr__(self) -> str:
        return self.__str__() 