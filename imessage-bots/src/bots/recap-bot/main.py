"""Main application for the recap bot."""

import logging
import uuid
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn
import requests

import config
from models import WebhookData, MessageData
from message_tracker import MessageTracker
from message_summarizer import MessageSummarizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
message_tracker: MessageTracker = None
message_summarizer: MessageSummarizer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    global message_tracker, message_summarizer
    
    logger.info("Starting Recap Bot...")
    
    # Validate configuration
    try:
        config.validate_config()
        logger.info("✅ Configuration validated successfully")
    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        raise
    
    # Initialize components
    message_tracker = MessageTracker()
    message_summarizer = MessageSummarizer()
    
    logger.info(f"🤖 {config.BOT_NAME} v{config.BOT_VERSION} started successfully")
    logger.info(f"🎯 Listening for '{config.TRIGGER_PHRASE}' commands")
    logger.info(f"📱 Using BlueBubbles isFromMe flag to identify your messages")
    
    yield
    
    logger.info("Shutting down Recap Bot...")

# Create FastAPI app
app = FastAPI(
    title=config.BOT_NAME,
    description="iMessage bot that recaps unread messages in group chats",
    version=config.BOT_VERSION,
    lifespan=lifespan
)

@app.get("/")
async def health_check():
    """Health check endpoint."""
    stats = message_tracker.get_stats() if message_tracker else {}
    return {
        "status": "healthy",
        "bot": config.BOT_NAME,
        "version": config.BOT_VERSION,
        "trigger": config.TRIGGER_PHRASE,
        "stats": stats
    }

@app.post("/webhook")
async def handle_webhook(webhook_data: WebhookData, background_tasks: BackgroundTasks):
    """
    Handle incoming webhooks from BlueBubbles.
    
    Args:
        webhook_data: The webhook data from BlueBubbles
        background_tasks: FastAPI background tasks
    """
    try:
        print(f"🔥 WEBHOOK RECEIVED: type={webhook_data.type}")
        print(f"🔥 WEBHOOK DATA: {webhook_data.data}")
        
        if webhook_data.type not in ["message", "updated-message", "new-message"]:
            print(f"🔥 IGNORING: Not a message type (got: {webhook_data.type})")
            return {"status": "ignored", "reason": "not a message"}
        
        message_data = MessageData(**webhook_data.data)
        print(f"🔥 MESSAGE DATA: text='{message_data.text}', isFromMe={message_data.isFromMe}")
        
        # Skip messages without text
        if not message_data.text:
            print(f"🔥 IGNORING: No text content")
            return {"status": "ignored", "reason": "no text content"}
        
        # Get chat GUID - different webhook types have different structures
        chat_guid = None
        
        # Check for chats array first (new-message webhook)
        if webhook_data.data.get('chats'):
            chats = webhook_data.data.get('chats', [])
            if chats:
                chat_guid = chats[0].get('guid')
                print(f"🔥 CHAT GUID from chats array: {chat_guid}")
        elif message_data.chat:
            # Standard message webhook
            chat_guid = message_data.chat.get("guid")
            print(f"🔥 CHAT GUID from chat: {chat_guid}")
        else:
            # For updated-message webhooks, we can't get the chat GUID
            print(f"🔥 SKIPPING: {webhook_data.type} webhook without chat info - can't send response")
            return {"status": "ignored", "reason": f"{webhook_data.type} without chat info"}
            
        print(f"🔥 CHAT INFO: chat_data={message_data.chat}, chat_guid={chat_guid}")
        if not chat_guid:
            print(f"🔥 IGNORING: No chat GUID found")
            return {"status": "ignored", "reason": "no chat guid"}
        
        # Check if this is from the user (the person who can trigger recaps)
        is_from_user = message_data.isFromMe
        
        message_text = message_data.text.strip()
        print(f"🔍 DEBUG: Processing message from chat {chat_guid}: {message_text[:50]}...")
        print(f"🔍 DEBUG: isFromMe: {is_from_user}, trigger_phrase: '{config.TRIGGER_PHRASE}', message starts with trigger: {message_text.lower().startswith(config.TRIGGER_PHRASE.lower())}")
        
        # Check if this is a recap command from the user
        if is_from_user and message_text.lower().startswith(config.TRIGGER_PHRASE.lower()):
            # Process recap request in background
            background_tasks.add_task(process_recap_request, chat_guid, message_text)
        else:
            # Track this message as unread (unless it's from the user)
            if not is_from_user:
                message_tracker.update_message_count(
                    chat_guid, 
                    message_data.guid, 
                    message_data.dateCreated or 0
                )
            logger.debug(f"Tracked message in {chat_guid}")
        
        return {"status": "accepted"}
        
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        return {"status": "error", "message": str(e)}

def parse_message_count(message_text: str) -> int:
    """
    Parse message count from recap command.
    
    Args:
        message_text: The message text (e.g., "!recap 50", "!recap 100")
        
    Returns:
        Number of messages to recap (default: 50)
    """
    import re
    
    # Default to 50 messages if no count specified
    default_count = 50
    
    # Extract number from command (e.g., "!recap 100")
    # Look for digits after the trigger phrase
    number_match = re.search(r'!recap\s+(\d+)', message_text.lower())
    if not number_match:
        return default_count
    
    count = int(number_match.group(1))
    
    # Limit to reasonable range (1-500 messages)
    if count < 1:
        return 1
    elif count > 500:
        return 500
    
    return count

async def process_recap_request(chat_guid: str, message_text: str):
    """
    Process a recap request from the user.
    
    Args:
        chat_guid: The GUID of the chat
        message_text: The message text containing the recap command
    """
    try:
        logger.info(f"Processing recap request for chat {chat_guid}")
        
        # Parse message count from command (e.g., "!recap 50")
        message_count = parse_message_count(message_text)
        
        await send_message(chat_guid, f"📊 Analyzing the last {message_count} messages... This may take a moment.")
        
        # Fetch extra messages to account for filtering out user's own messages
        # Add some buffer to ensure we get enough non-user messages
        fetch_limit = message_count + 20  # Get extra messages to account for user's messages being filtered out
        
        # Fetch messages from BlueBubbles (no timestamp filter, just get recent messages)
        raw_messages = message_summarizer.get_messages_from_bluebubbles(
            chat_guid, 
            since_timestamp=None,  # Get all recent messages
            limit=fetch_limit      # Fetch more than requested to account for filtering
        )
        
        if not raw_messages:
            await send_message(chat_guid, f"📖 No messages found. Try checking if the chat has any recent messages.")
            return
        
        # Process and summarize messages
        processed_messages = message_summarizer.process_messages(raw_messages)
        
        # Filter out messages from the user (we don't need to recap our own messages)
        messages_to_summarize = [msg for msg in processed_messages if not msg.is_from_user]
        
        # Limit to the requested message count after filtering
        messages_to_summarize = messages_to_summarize[:message_count]
        
        if not messages_to_summarize:
            await send_message(chat_guid, f"📖 All of the recent messages are from you! Nothing new to recap.")
            return
        
        # Generate summary
        recap_response = message_summarizer.generate_summary(messages_to_summarize, chat_guid)
        
        # Format and send the recap
        recap_message = format_recap_message(recap_response)
        await send_message(chat_guid, recap_message)
        
        logger.info(f"Successfully processed recap for {chat_guid}")
        
    except Exception as e:
        logger.error(f"Error processing recap request for chat {chat_guid}: {e}")
        await send_message(chat_guid, "❌ Sorry, something went wrong while generating your recap. Please try again.")

def format_recap_message(recap: Any) -> str:
    """
    Format the recap response into a readable message.
    
    Args:
        recap: RecapResponse object
        
    Returns:
        Formatted recap message
    """
    # Create a single paragraph with all the info
    participants_text = f" ({', '.join(recap.participants)})" if recap.participants else ""
    time_text = f" from {recap.time_range}" if recap.time_range else ""
    
    message = f"📋 Recap of {recap.messages_analyzed} messages{participants_text}{time_text}: {recap.summary}"
    
    return message

async def send_message(chat_guid: str, text: str, method: str = "apple-script"):
    """
    Send a message via BlueBubbles API.
    
    Args:
        chat_guid: The GUID of the chat to send to
        text: The message text
        method: The method to use for sending (default: apple-script)
    """
    try:
        params = {"password": config.BLUEBUBBLES_PASSWORD}
        data = {
            "chatGuid": chat_guid,
            "tempGuid": str(uuid.uuid4()),
            "message": text,
            "method": method,
            "subject": "",
            "effectId": "",
            "selectedMessageGuid": ""
        }
        
        url = f"{config.BLUEBUBBLES_SERVER_URL}/api/v1/message/text"
        
        logger.info(f"Sending recap message to {chat_guid}: {text[:50]}...")
        
        response = requests.post(
            url,
            json=data,
            params=params,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        response.raise_for_status()
        logger.info(f"Successfully sent recap message to {chat_guid}")
        
    except requests.RequestException as e:
        logger.error(f"Failed to send message to BlueBubbles: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error sending message: {e}")
        raise

@app.get("/stats")
async def get_stats():
    """Get bot statistics."""
    if not message_tracker:
        return {"error": "Bot not initialized"}
    
    return {
        "bot": config.BOT_NAME,
        "version": config.BOT_VERSION,
        "trigger": config.TRIGGER_PHRASE,
        "stats": message_tracker.get_stats()
    }

@app.post("/mark-read/{chat_guid}")
async def mark_chat_read(chat_guid: str):
    """Manually mark a chat as read (useful for testing)."""
    if not message_tracker:
        return {"error": "Bot not initialized"}
    
    # Mark as read with current timestamp
    import time
    current_timestamp = int(time.time() * 1000)
    message_tracker.mark_as_read(chat_guid, f"manual-{current_timestamp}", current_timestamp)
    
    return {
        "status": "success",
        "message": f"Marked {chat_guid} as read",
        "unread_count": message_tracker.get_unread_count(chat_guid)
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=True,
        log_level="info"
    ) 