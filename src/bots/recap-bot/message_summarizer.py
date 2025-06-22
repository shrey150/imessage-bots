"""Message summarization using OpenAI for the recap bot."""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from openai import OpenAI
import requests
import config
from models import MessageSummary, RecapResponse

logger = logging.getLogger(__name__)

class MessageSummarizer:
    """Handles message summarization using OpenAI."""
    
    def __init__(self):
        """Initialize the message summarizer."""
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
    
    def get_messages_from_bluebubbles(self, chat_guid: str, since_timestamp: Optional[int] = None, limit: int = 200) -> List[Dict[str, Any]]:
        """
        Fetch messages from BlueBubbles API.
        
        Args:
            chat_guid: The GUID of the chat
            since_timestamp: Only get messages after this timestamp
            limit: Maximum number of messages to fetch
            
        Returns:
            List of message dictionaries
        """
        try:
            params = {
                "password": config.BLUEBUBBLES_PASSWORD,
                "limit": limit,
                "sort": "DESC"  # Get newest messages first
            }
            
            if since_timestamp:
                params["after"] = since_timestamp
            
            url = f"{config.BLUEBUBBLES_SERVER_URL}/api/v1/chat/{chat_guid}/message"
            
            logger.info(f"Fetching messages from {chat_guid} since {since_timestamp}")
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            messages = data.get("data", [])
            
            logger.info(f"Retrieved {len(messages)} messages from BlueBubbles")
            return messages
            
        except requests.RequestException as e:
            logger.error(f"Error fetching messages from BlueBubbles: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching messages: {e}")
            return []
    
    def process_messages(self, messages: List[Dict[str, Any]]) -> List[MessageSummary]:
        """
        Process raw messages into MessageSummary objects.
        
        Args:
            messages: Raw message data from BlueBubbles
            
        Returns:
            List of processed MessageSummary objects
        """
        processed_messages = []
        
        for msg in messages:
            try:
                # Skip messages without text content
                if not msg.get("text"):
                    continue
                
                # Determine sender
                sender = "Unknown"
                is_from_user = msg.get("isFromMe", False)
                
                if is_from_user:
                    sender = "You"
                elif msg.get("handle") and msg["handle"].get("address"):
                    sender = msg["handle"]["address"]
                    # Try to get a nicer display name
                    if msg["handle"].get("displayName"):
                        sender = msg["handle"]["displayName"]
                
                # Convert timestamp
                timestamp = datetime.fromtimestamp(msg.get("dateCreated", 0) / 1000)
                
                processed_messages.append(MessageSummary(
                    sender=sender,
                    timestamp=timestamp,
                    content=msg["text"],
                    is_from_user=is_from_user
                ))
                
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                continue
        
        # Sort by timestamp (oldest first for chronological summary)
        processed_messages.sort(key=lambda x: x.timestamp)
        
        logger.info(f"Processed {len(processed_messages)} messages for summarization")
        return processed_messages
    
    def generate_summary(self, messages: List[MessageSummary], chat_guid: str) -> RecapResponse:
        """
        Generate a summary of messages using OpenAI.
        
        Args:
            messages: List of messages to summarize
            chat_guid: The GUID of the chat
            
        Returns:
            RecapResponse with summary and key points
        """
        try:
            if not messages:
                return RecapResponse(
                    chat_guid=chat_guid,
                    unread_count=0,
                    messages_analyzed=0,
                    summary="No unread messages to summarize.",
                    key_points=[],
                    participants=[],
                    time_range=""
                )
            
            # Prepare conversation text for OpenAI
            conversation_text = self._format_messages_for_ai(messages)
            
            # Get participants and time range
            participants = list(set(msg.sender for msg in messages if msg.sender != "You"))
            time_range = self._get_time_range(messages)
            
            # Create the prompt
            prompt = self._create_summary_prompt(conversation_text, len(messages))
            
            # Call OpenAI
            response = self.client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that summarizes group chat conversations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=config.MAX_SUMMARY_LENGTH,
                temperature=0.3
            )
            
            summary_text = response.choices[0].message.content.strip()
            
            # Extract key points (simple approach - split by bullet points or numbers)
            key_points = self._extract_key_points(summary_text)
            
            return RecapResponse(
                chat_guid=chat_guid,
                unread_count=len(messages),
                messages_analyzed=len(messages),
                summary=summary_text,
                key_points=key_points,
                participants=participants,
                time_range=time_range
            )
            
        except Exception as e:
            logger.error(f"Error generating summary with OpenAI: {e}")
            return RecapResponse(
                chat_guid=chat_guid,
                unread_count=len(messages),
                messages_analyzed=len(messages),
                summary=f"Unable to generate summary due to error: {str(e)}",
                key_points=["Error occurred during summarization"],
                participants=list(set(msg.sender for msg in messages if msg.sender != "You")),
                time_range=self._get_time_range(messages)
            )
    
    def _format_messages_for_ai(self, messages: List[MessageSummary]) -> str:
        """Format messages for AI processing."""
        formatted_messages = []
        
        for msg in messages:
            timestamp_str = msg.timestamp.strftime("%m/%d %I:%M%p")
            formatted_messages.append(f"[{timestamp_str}] {msg.sender}: {msg.content}")
        
        return "\n".join(formatted_messages)
    
    def _get_time_range(self, messages: List[MessageSummary]) -> str:
        """Get the time range of messages."""
        if not messages:
            return ""
        
        start_time = messages[0].timestamp
        end_time = messages[-1].timestamp
        
        if start_time.date() == end_time.date():
            return f"{start_time.strftime('%B %d')} from {start_time.strftime('%I:%M%p')} to {end_time.strftime('%I:%M%p')}"
        else:
            return f"{start_time.strftime('%B %d %I:%M%p')} to {end_time.strftime('%B %d %I:%M%p')}"
    
    def _create_summary_prompt(self, conversation_text: str, message_count: int) -> str:
        """Create the prompt for OpenAI summarization."""
        return f"""Please summarize this group chat conversation with {message_count} messages in ONE SHORT paragraph only. 

Focus on:
- Main topics discussed
- Important decisions or plans made
- Key information shared
- Any urgent matters or questions

Keep the summary concise and informative. Write it as a single short paragraph without any markdown formatting, bullet points, special characters, or emojis. Use plain text only with no symbols or decorative elements.

Conversation:
{conversation_text}

Please provide a clear, short single-paragraph summary with no emojis that helps someone quickly understand what they missed."""
    
    def _extract_key_points(self, summary_text: str) -> List[str]:
        """Extract key points from the summary text."""
        key_points = []
        
        # Look for bullet points or numbered lists
        lines = summary_text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                key_points.append(line[1:].strip())
            elif line and line[0].isdigit() and '.' in line:
                # Handle numbered lists like "1. Something"
                key_points.append(line.split('.', 1)[1].strip())
        
        # If no bullet points found, try to extract sentences
        if not key_points:
            sentences = summary_text.split('.')
            key_points = [s.strip() for s in sentences[:3] if s.strip()]
        
        return key_points[:5]  # Limit to 5 key points 