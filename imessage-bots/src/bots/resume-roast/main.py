import asyncio
import logging
import uuid
import requests
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn

from config import config
from models import WebhookData, ConversationState
from conversation_state import conversation_manager
from stagehand_scraper import stagehand_linkedin_scraper
from roast_generator import roast_generator

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
    logger.info("Starting Resume Roast Bot...")
    try:
        config.validate()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Resume Roast Bot...")

app = FastAPI(
    title="Resume Roast Bot",
    description="A snarky resume roasting chatbot for iMessage via BlueBubbles",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def health_check():
    """Health check endpoint."""
    stats = conversation_manager.get_stats()
    return {
        "status": "ok",
        "message": "Resume Roast Bot is running!",
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
        
        # Only process messages from the configured chat
        if chat_guid != config.CHAT_GUID:
            logger.info(f"Ignoring message from chat {chat_guid} (not configured chat)")
            return {"status": "ignored", "reason": "not from configured chat"}
        
        logger.info(f"Processing message from chat {chat_guid}: {message_text[:50]}...")
        
        # Process the message in the background
        background_tasks.add_task(process_message, chat_guid, message_text)
        
        return {"status": "accepted"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def process_message(chat_guid: str, message_text: str):
    """
    Process an incoming message and generate appropriate response.
    
    Args:
        chat_guid: The GUID of the chat
        message_text: The text content of the message
    """
    try:
        # Get or create conversation state
        conversation = conversation_manager.start_conversation(chat_guid)
        logger.info(f"Processing message for conversation state: {conversation.state}")
        
        if conversation.state == ConversationState.WAITING_FOR_LINKEDIN:
            await handle_linkedin_request(chat_guid, message_text, conversation)
        elif conversation.state == ConversationState.PROCESSING:
            # Already processing, send a wait message
            await send_message(chat_guid, "Hold your horses! I'm still analyzing your career disasters... ⏳")
        
    except Exception as e:
        logger.error(f"Error processing message for chat {chat_guid}: {e}")
        # Send an error message to the user
        await send_message(chat_guid, "Oops! Something went wrong. Even my roasting skills have limits apparently... 😅")

async def handle_linkedin_request(chat_guid: str, message_text: str, conversation):
    """
    Handle LinkedIn URL request and validation.
    
    Args:
        chat_guid: The GUID of the chat
        message_text: The text content of the message
        conversation: The conversation state object
    """
    # Check if message contains a LinkedIn URL
    if "linkedin.com" in message_text.lower():
        # Extract potential URLs from the message
        import re
        url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+|linkedin\.com[^\s<>"]*'
        urls = re.findall(url_pattern, message_text, re.IGNORECASE)
        
        linkedin_url = None
        for url in urls:
            if "linkedin.com" in url.lower():
                linkedin_url = url
                break
        
        if linkedin_url and stagehand_linkedin_scraper.is_valid_linkedin_url(linkedin_url):
            # Valid LinkedIn URL found - start processing
            logger.info(f"Valid LinkedIn URL received: {linkedin_url}")
            
            # Update conversation state
            conversation_manager.update_conversation(
                chat_guid,
                state=ConversationState.PROCESSING,
                linkedin_url=linkedin_url
            )
            
            await send_message(chat_guid, "aight. please wait while you waste my time...")
            
            # Process the LinkedIn profile
            await process_linkedin_profile(chat_guid, linkedin_url)
            
        else:
            # Invalid LinkedIn URL
            logger.info(f"Invalid LinkedIn URL received: {linkedin_url}")
            response = roast_generator.generate_invalid_url_message()
            await send_message(chat_guid, response)
    
    else:
        # No LinkedIn URL provided - send prompt message
        response = roast_generator.generate_linkedin_prompt_message(conversation.message_count)
        await send_message(chat_guid, response)

async def process_linkedin_profile(chat_guid: str, linkedin_url: str):
    """
    Scrape LinkedIn profile and generate roast.
    
    Args:
        chat_guid: The GUID of the chat
        linkedin_url: The LinkedIn profile URL
    """
    try:
        logger.info(f"Starting LinkedIn profile analysis for: {linkedin_url}")
        
        # Scrape the LinkedIn profile using Stagehand
        profile = await stagehand_linkedin_scraper.scrape_profile(linkedin_url)
        
        logger.info(f"Scraper returned profile: {profile}")
        logger.info(f"Profile type: {type(profile)}")
        
        if not profile:
            logger.warning(f"Failed to scrape LinkedIn profile: {linkedin_url}")
            await send_message(
                chat_guid, 
                "LinkedIn is being more protective than your job security right now. Can't access your profile - they're onto us! 🤖🔒"
            )
            # Reset conversation state
            conversation_manager.update_conversation(chat_guid, state=ConversationState.WAITING_FOR_LINKEDIN)
            return
        
        # Update conversation with profile data
        conversation_manager.update_conversation(
            chat_guid,
            profile_data=profile
        )
        
        # Generate the roast
        logger.info(f"Generating roast for profile: {profile.name}")
        roast = roast_generator.generate_roast(profile)
        
        if roast:
            await send_message(chat_guid, roast)
            logger.info(f"Roast delivered successfully for chat {chat_guid}")
        else:
            await send_message(
                chat_guid,
                "I tried to roast your career but honestly... it's already well-done. 🔥😬"
            )
        
        # Reset conversation state for potential new roasts
        conversation_manager.update_conversation(chat_guid, state=ConversationState.WAITING_FOR_LINKEDIN)
        
    except Exception as e:
        logger.error(f"Error processing LinkedIn profile: {e}")
        await send_message(
            chat_guid,
            "Something went wrong while analyzing your profile. Maybe that's for the best... 😅"
        )
        # Reset conversation state
        conversation_manager.update_conversation(chat_guid, state=ConversationState.WAITING_FOR_LINKEDIN)

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
        
        response = requests.post(
            url,
            json=data,
            params=params,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        response.raise_for_status()
        logger.info(f"Message sent successfully to chat {chat_guid}")
        
    except requests.RequestException as e:
        logger.error(f"Failed to send message to BlueBubbles: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error sending message: {e}")
        raise

@app.get("/stats")
async def get_stats():
    """Get conversation statistics."""
    return conversation_manager.get_stats()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        log_level="info" if config.DEBUG else "warning"
    ) 