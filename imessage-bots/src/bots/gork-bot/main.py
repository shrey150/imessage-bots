import asyncio
import logging
import requests
from typing import Optional
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn

from config import config
from models import WebhookData, GorkResponse
from conversation_state import chat_history
from gork_ai import gork_ai

# Configure logging
logging.basicConfig(
    level=logging.INFO if config.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app."""
    # Startup
    logger.info("Starting Gork Bot...")
    try:
        config.validate()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Gork Bot...")

app = FastAPI(
    title="Gork Bot",
    description="A sarcastic and snarky bot that explains previous messages with wit and humor",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def health_check():
    """Health check endpoint."""
    stats = chat_history.get_stats()
    return {
        "status": "ok",
        "message": "Gork Bot is running and ready to be sarcastic!",
        "trigger_phrase": config.TRIGGER_PHRASE,
        "chat_guid": config.CHAT_GUID,
        "stats": stats
    }

@app.post("/webhook")
async def handle_webhook(webhook_data: WebhookData, background_tasks: BackgroundTasks):
    """
    Handle incoming webhooks from BlueBubbles.
    
    This endpoint receives new message events and processes them asynchronously.
    """
    try:
        logger.info(f"Received webhook: {webhook_data.type}")
        
        # Only handle new-message events
        if webhook_data.type != "new-message":
            logger.info(f"Ignoring webhook type: {webhook_data.type}")
            return {"status": "ignored", "reason": "not a new message"}
        
        # Validate message data
        if not webhook_data.data:
            logger.warning("Webhook missing message data")
            return {"status": "error", "reason": "missing message data"}
        
        message = webhook_data.data
        
        # Ignore messages from me (the bot)
        if message.isFromMe:
            logger.info("Ignoring message from bot")
            return {"status": "ignored", "reason": "message from bot"}
        
        # Ensure we have chat information
        if not message.chats:
            logger.warning("Message missing chat information")
            return {"status": "error", "reason": "missing chat information"}
        
        chat_guid = message.chats[0].guid
        message_text = message.text or ""
        message_guid = message.guid
        
        logger.info(f"Processing message from chat {chat_guid}: {message_text[:50]}...")
        
        # Only process messages from the configured chat
        if chat_guid != config.CHAT_GUID:
            logger.info(f"Ignoring message from chat {chat_guid}, not matching configured CHAT_GUID {config.CHAT_GUID}")
            return {"status": "ignored", "reason": "message not from configured chat"}
        
        logger.info(f"✅ MESSAGE FROM CORRECT CHAT - Processing message: '{message_text}' from configured chat {chat_guid}")
        
        # Add message to chat history for context (including message GUID)
        chat_history.add_message(chat_guid, message_text, message_guid)
        
        # Check if message starts with trigger phrase
        message_lower = message_text.strip().lower()
        trigger_lower = config.TRIGGER_PHRASE.lower()
        
        logger.info(f"🔍 CHECKING TRIGGER - Message starts with: '{message_text[:20]}...', Trigger: '{config.TRIGGER_PHRASE}', Match: {message_lower.startswith(trigger_lower)}")
        
        if message_lower.startswith(trigger_lower):
            # Log that a gork message was received
            logger.info(f"🤖 GORK TRIGGER RECEIVED - Chat: {chat_guid}, Trigger message: '{message_text}', GUID: {message_guid}")
            logger.info(f"🎯 WILL ANALYZE PREVIOUS MESSAGE - Looking for message that came before this @gork trigger")
            # Process the Gork request in the background
            background_tasks.add_task(process_gork_request, chat_guid, message_text)
        else:
            logger.info(f"❌ NO TRIGGER MATCH - Message: '{message_text}', Expected trigger: '{config.TRIGGER_PHRASE}'")
        
        return {"status": "accepted"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def process_gork_request(chat_guid: str, message_text: str):
    """
    Process a Gork request to explain a previous message sarcastically.
    
    Args:
        chat_guid: The GUID of the chat
        message_text: The text content of the message with the @gork trigger
    """
    try:
        logger.info(f"🔍 PROCESSING GORK REQUEST - Chat: {chat_guid}, Trigger: '{message_text}'")
        
        # Extract the request after the trigger phrase
        request_text = message_text[len(config.TRIGGER_PHRASE):].strip()
        
        if not request_text:
            logger.info("❌ Empty gork request - sending help message")
            await send_message(chat_guid, 
                "oh wow, summoning me with zero instructions. classic move from someone who probably thinks "
                "mysterious silence is compelling. try '@gork explain what they meant' or '@gork why is this "
                "funny' next time. i'm here to roast messages, not read your mind")
            return
        
        # Get the previous message to explain (text and GUID)
        previous_message_data = chat_history.get_previous_message(chat_guid)
        
        # Log the current chat history for debugging
        recent_messages = chat_history.get_recent_messages(chat_guid, 5)
        logger.info(f"📚 CHAT HISTORY - Recent messages count: {len(recent_messages)}")
        for i, msg in enumerate(recent_messages):
            logger.info(f"📝 Message {i+1}: '{msg[:100]}{'...' if len(msg) > 100 else ''}'")
        
        if not previous_message_data:
            logger.info("❌ No previous message found to explain")
            await send_message(chat_guid,
                "asking me to explain a previous message when there isn't one. brilliant logic from someone "
                "who probably thinks starting conversations is optional. maybe try having an actual chat first")
            return
        
        previous_message_text, previous_message_guid = previous_message_data
        
        # Log what message is being processed
        logger.info(f"📝 TARGET MESSAGE FOUND - Message GUID: {previous_message_guid}, "
                   f"Text: '{previous_message_text[:100]}{'...' if len(previous_message_text) > 100 else ''}', "
                   f"User request: '{request_text}'")
        logger.info(f"🎯 ANALYZING: The message that came BEFORE the @gork trigger will be explained")
        
        # Get additional context
        context_messages = chat_history.get_recent_messages(chat_guid, 3)
        logger.info(f"📚 CONTEXT - Retrieved {len(context_messages)} recent messages for context")
        
        # Generate sarcastic explanation
        explanation = await gork_ai.generate_sarcastic_explanation(
            user_request=request_text,
            previous_message=previous_message_text,
            context_messages=context_messages
        )
        
        # Send the sarcastic explanation
        await send_message(chat_guid, f"gork's analysis:\n\n{explanation}")
        
        logger.info(f"✅ GORK RESPONSE SENT - Chat: {chat_guid}, Response length: {len(explanation)} chars")
        
    except Exception as e:
        logger.error(f"❌ ERROR PROCESSING GORK REQUEST - Chat: {chat_guid}, Error: {e}")
        await send_message(chat_guid, 
            "great, something broke while i was preparing to roast your message. how fitting. "
            "try again i guess")



async def send_message(chat_guid: str, text: str, method: str = "apple-script"):
    """
    Send a message to a chat via BlueBubbles.
    
    Args:
        chat_guid: The GUID of the chat to send the message to
        text: The text content of the message
        method: The method to use for sending (default: apple-script)
    """
    try:
        url = f"{config.BLUEBUBBLES_SERVER_URL}/api/v1/message/text"
        
        # Generate a unique temporary GUID for this message
        import uuid
        temp_guid = str(uuid.uuid4())
        
        payload = {
            "chatGuid": chat_guid,
            "tempGuid": temp_guid,
            "message": text,
            "method": method,
            "subject": "",
            "effectId": "",
            "selectedMessageGuid": ""
        }
        
        params = {
            "password": config.BLUEBUBBLES_PASSWORD
        }
        
        logger.info(f"Sending message to chat {chat_guid}: {text[:50]}...")
        logger.info(f"Request payload: {payload}")
        logger.info(f"Request URL: {url}")
        
        response = requests.post(url, json=payload, params=params, timeout=10)
        
        # Log response details for debugging
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response text: {response.text}")
        
        response.raise_for_status()
        
        logger.info(f"Message sent successfully to chat {chat_guid}")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending message to chat {chat_guid}: {e}")
        # Log more details about the request that failed
        logger.error(f"Failed request URL: {url}")
        logger.error(f"Failed request params: {params}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error sending message: {e}")
        raise

@app.get("/stats")
async def get_stats():
    """Get bot statistics."""
    stats = chat_history.get_stats()
    return {
        "chat_history": stats,
        "config": {
            "trigger_phrase": config.TRIGGER_PHRASE,
            "chat_guid": config.CHAT_GUID,
            "bluebubbles_url": config.BLUEBUBBLES_SERVER_URL
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG
    ) 