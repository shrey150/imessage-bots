"""
Lover Bot SDK - An AI girlfriend bot built with the iMessage Bot Framework.
Provides context-aware romantic messaging with reactive responses only.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from imessage_bot_framework import Bot, State
from imessage_bot_framework.decorators import only_from_me

from config import config
from lover_ai import LoverAI
from conversation_state import ConversationManager

# Configure logging
logging.basicConfig(
    level=logging.INFO if config.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize components
bot = Bot(f"Lover Bot SDK ({config.LOVER_NAME})", port=config.PORT, debug=config.DEBUG)
lover_ai = LoverAI()
conversation_manager = ConversationManager()
state = State("lover_bot_sdk_state.json")

# Background task for first message only
first_message_sent = False
background_tasks_started = False

def validate_config():
    """Validate configuration without starting async tasks."""
    logger.info(f"Starting Lover Bot SDK ({config.LOVER_NAME})...")
    
    try:
        config.validate()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise

async def start_background_tasks():
    """Start background tasks after the event loop is running (only once)."""
    global first_message_sent, background_tasks_started
    
    # Only start once
    if background_tasks_started:
        return
    
    background_tasks_started = True
    logger.info("Starting background tasks...")
    
    # Send first message after a short delay
    await asyncio.sleep(2)  # Wait for server to be ready
    if not first_message_sent:
        await send_first_message()
        first_message_sent = True
        logger.info("First message sent - now only responding to incoming messages")

@bot.on_message
def handle_message(message):
    """Handle incoming messages with context-aware responses."""
    # Start background tasks only once when first message is received
    if not background_tasks_started:
        asyncio.create_task(start_background_tasks())
    
    # Only process messages in our configured chat
    if message.chat_guid != config.CHAT_GUID:
        logger.info(f"Ignoring message from different chat: {message.chat_guid}")
        return None
    
    # Ignore messages from me (the bot)
    if message.is_from_me:
        logger.info("Ignoring message from bot")
        return None
    
    logger.info(f"Processing message from {config.USER_NAME}: {message.text[:50]}...")
    
    # Process message asynchronously in background
    asyncio.create_task(process_user_message_async(message))
    
    # Return None to not send immediate response (we'll handle it async)
    return None

async def process_user_message_async(message):
    """Process user message asynchronously."""
    try:
        # Process the message and update conversation context
        conversation = conversation_manager.process_user_message(message.chat_guid, message.text)
        logger.info(f"Processing message for conversation state: {conversation.state}")
        logger.info(f"User mood detected: {conversation.user_mood}")
        
        # Get comprehensive conversation context for AI
        context = conversation_manager.get_conversation_context(message.chat_guid)
        
        # Generate contextually appropriate response
        response = await lover_ai.generate_response_to_user(message.text, context)
        
        # Send the response
        bot.send_to_chat(response, message.chat_guid)
        
        # Mark message as sent in conversation manager
        conversation_manager.mark_message_sent(message.chat_guid, response)
        
        logger.info(f"Sent contextual response: {response[:50]}...")
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        # Send a contextual error message
        fallback = await get_fallback_error_message(message.chat_guid)
        bot.send_to_chat(fallback, message.chat_guid)

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
    """Send the very first message when the bot starts."""
    try:
        logger.info("Sending first message...")
        
        # Get conversation context (will be new conversation)
        context = conversation_manager.get_conversation_context(config.CHAT_GUID)
        
        # Generate a special first message
        first_message = await lover_ai.generate_proactive_message(context)
        
        # Send to the configured chat
        bot.send_to_chat(first_message, config.CHAT_GUID)
        
        # Mark message as sent
        conversation_manager.mark_message_sent(config.CHAT_GUID, first_message)
        
        logger.info(f"Sent first message: {first_message[:50]}...")
        
    except Exception as e:
        logger.error(f"Error sending first message: {e}")

# Admin commands (only respond to messages from me)
@bot.on_message
@only_from_me()
def admin_commands(message):
    """Handle admin commands from the bot owner."""
    if message.text.startswith("!lover"):
        parts = message.text.split()
        
        if len(parts) == 1 or parts[1] == "status":
            # Show status
            stats = conversation_manager.get_stats()
            lover_stats = lover_ai.get_stats()
            
            status_msg = f"""🤖 Lover Bot SDK Status:
• Lover: {config.LOVER_NAME}
• User: {config.USER_NAME}
• Mode: Reactive only (no automatic messages)
• Chat: {config.CHAT_GUID[:20]}...

📊 Stats:
• Conversations: {stats['total_conversations']}
• Messages sent: {stats['total_messages_sent']}
• Active chats: {stats['active_conversations']}
• AI requests: {lover_stats['total_requests']}"""
            
            return status_msg
            
        elif parts[1] == "send":
            # Force send a message
            asyncio.create_task(force_send_message_async())
            return "✅ Sending manual message..."
                
        elif parts[1] == "reset":
            # Reset conversation state
            conversation_manager.clear_conversation(config.CHAT_GUID)
            return "✅ Conversation state reset"
    
    return None

async def force_send_message_async():
    """Force send a message asynchronously (manual trigger only)."""
    try:
        context = conversation_manager.get_conversation_context(config.CHAT_GUID)
        message_text = await lover_ai.generate_proactive_message(context)
        
        bot.send_to_chat(message_text, config.CHAT_GUID)
        conversation_manager.mark_message_sent(config.CHAT_GUID, message_text)
        
        logger.info(f"Force sent message: {message_text[:50]}...")
    except Exception as e:
        logger.error(f"Error force sending message: {e}")

# Add custom FastAPI routes to the bot's app
@bot.app.get("/")
async def health_check():
    """Health check endpoint."""
    stats = conversation_manager.get_stats()
    lover_stats = lover_ai.get_stats()
    
    return {
        "status": "ok",
        "message": f"Lover Bot SDK ({config.LOVER_NAME}) is running and loving you!",
        "mode": "reactive_only",
        "config": {
            "lover_name": config.LOVER_NAME,
            "user_name": config.USER_NAME,
            "chat_guid": config.CHAT_GUID
        },
        "conversation_stats": stats,
        "ai_stats": lover_stats
    }

@bot.app.post("/send-message")
async def force_send_message():
    """Force send a proactive message (manual trigger only)."""
    try:
        context = conversation_manager.get_conversation_context(config.CHAT_GUID)
        message_text = await lover_ai.generate_proactive_message(context)
        
        bot.send_to_chat(message_text, config.CHAT_GUID)
        conversation_manager.mark_message_sent(config.CHAT_GUID, message_text)
        
        return {"status": "success", "message": message_text}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@bot.app.get("/stats")
async def get_stats():
    """Get detailed statistics."""
    return {
        "conversation_stats": conversation_manager.get_stats(),
        "ai_stats": lover_ai.get_stats(),
        "mode": "reactive_only",
        "config": {
            "lover_name": config.LOVER_NAME,
            "user_name": config.USER_NAME
        }
    }

if __name__ == "__main__":
    # Validate configuration before starting
    validate_config()
    
    # Run the bot
    bot.run(host=config.HOST) 