import asyncio
import logging
import requests
import uuid
from typing import Optional
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn

from config import config
from models import WebhookData
from lover_ai import lover_ai
from conversation_state import conversation_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO if config.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Background task for automatic messaging
messaging_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for FastAPI app."""
    global messaging_task
    
    # Startup
    logger.info("Starting Lover Bot...")
    try:
        config.validate()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise
    
    # Send first message immediately with context
    logger.info("Sending initial lover message...")
    await send_first_message()
    
    # Start background messaging task
    messaging_task = asyncio.create_task(automatic_messaging_loop())
    logger.info(f"Started automatic messaging every {config.MESSAGE_INTERVAL_MINUTES} minutes")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Lover Bot...")
    if messaging_task:
        messaging_task.cancel()
        try:
            await messaging_task
        except asyncio.CancelledError:
            logger.info("Automatic messaging task cancelled")

app = FastAPI(
    title="Lover Bot",
    description="An AI lover bot that texts you like your significant other with context-aware reactive messaging",
    version="2.0.0",
    lifespan=lifespan
)

@app.get("/")
async def health_check():
    """Health check endpoint."""
    stats = conversation_manager.get_stats()
    lover_stats = lover_ai.get_stats()
    return {
        "status": "ok",
        "message": f"Lover Bot ({config.LOVER_NAME}) is running and loving you!",
        "config": {
            "lover_name": config.LOVER_NAME,
            "user_name": config.USER_NAME,
            "message_interval_minutes": config.MESSAGE_INTERVAL_MINUTES,
            "chat_guid": config.CHAT_GUID
        },
        "conversation_stats": stats,
        "ai_stats": lover_stats
    }

@app.post("/webhook")
async def handle_webhook(webhook_data: WebhookData, background_tasks: BackgroundTasks):
    """
    Handle incoming webhooks from BlueBubbles with context-aware reactive messaging.
    
    The bot will analyze message context and respond appropriately based on conversation state.
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
        
        logger.info(f"Message received from chat: {chat_guid}")
        logger.info(f"Configured chat GUID: {config.CHAT_GUID}")
        logger.info(f"Message text: {message_text[:100]}...")
        
        # Only respond to messages in our configured chat
        if chat_guid != config.CHAT_GUID:
            logger.info(f"Ignoring message from different chat: {chat_guid}")
            return {"status": "ignored", "reason": "different chat"}
        
        logger.info(f"Processing message from {config.USER_NAME}: {message_text[:50]}...")
        
        # Process the message with context awareness in the background
        background_tasks.add_task(process_user_message, chat_guid, message_text)
        
        return {"status": "accepted", "message": "Processing your message with love!"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def process_user_message(chat_guid: str, message_text: str):
    """
    Process an incoming message with context awareness and generate appropriate response.
    
    Args:
        chat_guid: The GUID of the chat
        message_text: The text content of the message
    """
    try:
        # Process the message and update conversation context
        conversation = conversation_manager.process_user_message(chat_guid, message_text)
        logger.info(f"Processing message for conversation state: {conversation.state}")
        logger.info(f"User mood detected: {conversation.user_mood}")
        
        # Get comprehensive conversation context for AI
        context = conversation_manager.get_conversation_context(chat_guid)
        
        # Generate contextually appropriate response
        response = await lover_ai.generate_response_to_user(message_text, context)
        
        # Send the response
        await send_message(chat_guid, response)
        
        # Mark message as sent in conversation manager
        conversation_manager.mark_message_sent(chat_guid, response)
        
        logger.info(f"Sent contextual response: {response[:50]}...")
        
    except Exception as e:
        logger.error(f"Error processing message for chat {chat_guid}: {e}")
        # Send a contextual error message
        fallback = await get_fallback_error_message(chat_guid)
        await send_message(chat_guid, fallback)

async def get_fallback_error_message(chat_guid: str) -> str:
    """Get a contextual fallback message when there's an error."""
    conversation = conversation_manager.get_conversation(chat_guid)
    if conversation and conversation.user_mood == "sad":
        return f"i'm having trouble with my thoughts right now {config.USER_NAME.lower()}, but i'm still here for you"
    elif conversation and conversation.user_mood == "happy":
        return f"oops! my brain got excited seeing your message {config.USER_NAME.lower()}! i love you so much"
    else:
        return f"sorry {config.USER_NAME.lower()}, i'm having trouble with my thoughts right now but i love you"

async def send_first_message():
    """Send the very first message when the bot starts with context."""
    try:
        # Get conversation context (will be new conversation)
        context = conversation_manager.get_conversation_context(config.CHAT_GUID)
        
        # Generate a special first message (AI handles the greeting)
        first_message = await lover_ai.generate_proactive_message(context)
        
        await send_message(config.CHAT_GUID, first_message)
        
        # Mark message as sent
        conversation_manager.mark_message_sent(config.CHAT_GUID, first_message)
        
        logger.info(f"Sent first message: {first_message[:50]}...")
        
    except Exception as e:
        logger.error(f"Error sending first message: {e}")
        # Send a simple fallback first message
        fallback = f"hey {config.USER_NAME.lower()}! ur chaotic gf {config.LOVER_NAME.lower()} is online and thinking abt u"
        await send_message(config.CHAT_GUID, fallback)
        conversation_manager.mark_message_sent(config.CHAT_GUID, fallback)

async def automatic_messaging_loop():
    """Background task that sends contextually appropriate loving messages."""
    logger.info("Starting automatic messaging loop")
    
    # Wait a bit before starting the loop (since we already sent the first message)
    await asyncio.sleep(config.MESSAGE_INTERVAL_MINUTES * 60)
    
    while True:
        try:
            # Check if we should send a proactive message
            if conversation_manager.should_send_proactive_message(config.CHAT_GUID, config.MESSAGE_INTERVAL_MINUTES):
                logger.info("Generating automatic romantic message...")
                
                # Get current conversation context
                context = conversation_manager.get_conversation_context(config.CHAT_GUID)
                
                # Generate a proactive loving message with context
                message = await lover_ai.generate_proactive_message(context)
                
                # Send the message
                await send_message(config.CHAT_GUID, message)
                
                # Mark message as sent
                conversation_manager.mark_message_sent(config.CHAT_GUID, message)
                
                logger.info(f"Sent automatic message: {message[:50]}...")
            else:
                logger.info("Skipping automatic message - user awaiting response or too soon")
            
            # Wait for the next interval
            await asyncio.sleep(config.MESSAGE_INTERVAL_MINUTES * 60)
            
        except Exception as e:
            logger.error(f"Error in automatic messaging loop: {e}")
            # Wait a bit before retrying
            await asyncio.sleep(60)

async def send_message(chat_guid: str, text: str, method: str = "apple-script"):
    """
    Send a message using BlueBubbles API with improved error handling.
    
    Args:
        chat_guid: The chat GUID to send the message to
        text: The message text to send
        method: The method to use for sending ("apple-script" or "private-api")
    """
    try:
        url = f"{config.BLUEBUBBLES_SERVER_URL}/api/v1/message/text"
        
        payload = {
            "chatGuid": chat_guid,
            "tempGuid": str(uuid.uuid4()),
            "message": text,
            "method": method,
            "subject": "",
            "effectId": "",
            "selectedMessageGuid": ""
        }
        
        params = {"password": config.BLUEBUBBLES_PASSWORD}
        
        headers = {
            "Content-Type": "application/json"
        }
        
        logger.info(f"Sending message to {chat_guid}: {text[:50]}...")
        
        response = requests.post(url, json=payload, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            logger.info("Message sent successfully")
        else:
            logger.error(f"Failed to send message: {response.status_code} - {response.text}")
            raise Exception(f"BlueBubbles API error: {response.status_code}")
        
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise

@app.get("/stats")
async def get_stats():
    """Get comprehensive bot statistics."""
    conversation_stats = conversation_manager.get_stats()
    ai_stats = lover_ai.get_stats()
    return {
        "bot_name": config.LOVER_NAME,
        "user_name": config.USER_NAME,
        "message_interval_minutes": config.MESSAGE_INTERVAL_MINUTES,
        "conversation_stats": conversation_stats,
        "ai_stats": ai_stats
    }

@app.post("/send-message")
async def force_send_message():
    """Force send a contextually appropriate loving message immediately."""
    try:
        # Get current conversation context
        context = conversation_manager.get_conversation_context(config.CHAT_GUID)
        
        # Generate message with context
        message = await lover_ai.generate_proactive_message(context)
        
        await send_message(config.CHAT_GUID, message)
        
        # Mark message as sent
        conversation_manager.mark_message_sent(config.CHAT_GUID, message)
        
        return {"status": "success", "message": message, "context": context}
    except Exception as e:
        logger.error(f"Error force sending message: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message")

@app.get("/conversation/{chat_guid}")
async def get_conversation_info(chat_guid: str):
    """Get conversation information for a specific chat."""
    conversation = conversation_manager.get_conversation(chat_guid)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    context = conversation_manager.get_conversation_context(chat_guid)
    return {
        "conversation": conversation.dict(),
        "context": context
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG
    ) 