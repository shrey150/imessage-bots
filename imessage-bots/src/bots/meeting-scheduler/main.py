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
from meeting_parser import meeting_parser
from google_calendar import calendar_manager

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
    logger.info("Starting Meeting Scheduler Bot...")
    try:
        config.validate()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Meeting Scheduler Bot...")

app = FastAPI(
    title="Meeting Scheduler Bot",
    description="An intelligent meeting scheduler bot for iMessage via BlueBubbles",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def health_check():
    """Health check endpoint."""
    stats = conversation_manager.get_stats()
    return {
        "status": "ok",
        "message": "Meeting Scheduler Bot is running!",
        "trigger_phrase": config.TRIGGER_PHRASE,
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
        
        logger.info(f"Processing message from chat {chat_guid}: {message_text[:50]}...")
        
        # Check if message starts with trigger phrase or if we're in a conversation
        conversation = conversation_manager.get_conversation(chat_guid)
        
        if message_text.strip().lower().startswith(config.TRIGGER_PHRASE.lower()):
            # Process the meeting request in the background
            background_tasks.add_task(process_meeting_request, chat_guid, message_text)
        elif conversation and conversation.state == ConversationState.WAITING_FOR_EMAIL:
            # Process email response
            background_tasks.add_task(process_email_response, chat_guid, message_text)
        else:
            logger.info(f"Message doesn't start with trigger phrase '{config.TRIGGER_PHRASE}' and no active conversation")
        
        return {"status": "accepted"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def process_meeting_request(chat_guid: str, message_text: str):
    """
    Process a meeting scheduling request.
    
    Args:
        chat_guid: The GUID of the chat
        message_text: The text content of the message
    """
    try:
        # Get or create conversation state
        conversation = conversation_manager.start_conversation(chat_guid)
        logger.info(f"Processing meeting request for conversation state: {conversation.state}")
        
        # Extract the command after the trigger phrase
        command = message_text[len(config.TRIGGER_PHRASE):].strip()
        
        if not command:
            email_status = f" (Current email: {conversation.user_email})" if conversation.user_email else ""
            await send_message(chat_guid, f"📅 Hi! I'm your meeting scheduler bot. Use `!schedule` followed by your meeting request.\n\nExample: `!schedule Team standup tomorrow at 10am for 30 minutes with john@company.com`\n\n📧 I'll ask for your email address to add the meeting to your calendar too!{email_status}\n\n💡 To update your email, use: `!schedule email your@email.com`")
            return
        
        # Check if this is an email update command
        if command.lower().startswith("email "):
            new_email = command[6:].strip()
            if is_valid_email(new_email):
                conversation_manager.update_conversation(
                    chat_guid,
                    user_email=new_email
                )
                await send_message(chat_guid, f"✅ Email updated to: {new_email}")
            else:
                await send_message(chat_guid, "❌ That doesn't look like a valid email address. Please try again.")
            return
        
        # Check if we have the user's email, if not ask for it
        if not conversation.user_email:
            conversation_manager.update_conversation(
                chat_guid,
                state=ConversationState.WAITING_FOR_EMAIL,
                last_command=command
            )
            await send_message(chat_guid, "📧 To add this meeting to your calendar, I'll need your email address. Please reply with your email:")
            return
        
        # Process the meeting with the user's email
        await process_meeting_command(chat_guid, command, conversation.user_email)
        
    except Exception as e:
        logger.error(f"Error processing meeting request for chat {chat_guid}: {e}")
        await send_message(chat_guid, "❌ Oops! Something went wrong while processing your meeting request. Please try again.")
        conversation_manager.update_conversation(chat_guid, state=ConversationState.WAITING_FOR_COMMAND)

async def process_meeting_command(chat_guid: str, command: str, user_email: str):
    """
    Process a meeting command with the user's email.
    
    Args:
        chat_guid: The GUID of the chat
        command: The meeting command text
        user_email: The user's email address for calendar invite
    """
    try:
        # Update conversation state
        conversation_manager.update_conversation(
            chat_guid,
            state=ConversationState.PROCESSING
        )
        
        await send_message(chat_guid, "⏳ Processing your meeting request...")
        
        # Parse the meeting request using OpenAI
        meeting = meeting_parser.parse_meeting_request(command)
        
        if not meeting:
            await send_message(chat_guid, "❌ Sorry, I couldn't understand your meeting request. Please try again with more details like date, time, and participants.")
            conversation_manager.update_conversation(chat_guid, state=ConversationState.WAITING_FOR_COMMAND)
            return
        
        # Add the user's email to attendees if not already included
        if user_email not in meeting.attendees:
            meeting.attendees.append(user_email)
        
        # Validate meeting details
        is_valid, error_message = meeting_parser.validate_meeting_details(meeting)
        if not is_valid:
            await send_message(chat_guid, f"❌ {error_message}")
            conversation_manager.update_conversation(chat_guid, state=ConversationState.WAITING_FOR_COMMAND)
            return
        
        # Check availability (optional)
        if not calendar_manager.check_availability(meeting.start_datetime, meeting.end_datetime):
            await send_message(chat_guid, "⚠️ Warning: You appear to have a conflict during this time, but I'll create the meeting anyway.")
        
        # Create the meeting in Google Calendar
        meeting_url = calendar_manager.create_meeting(meeting)
        
        if meeting_url:
            # Format success message
            start_time = meeting.start_datetime.strftime("%B %d, %Y at %I:%M %p")
            end_time = meeting.end_datetime.strftime("%I:%M %p")
            
            success_message = f"✅ Meeting created successfully!\n\n"
            success_message += f"📝 **{meeting.title}**\n"
            success_message += f"🕐 {start_time} - {end_time}\n"
            
            if meeting.location:
                success_message += f"📍 {meeting.location}\n"
            
            if meeting.attendees:
                success_message += f"👥 Attendees: {', '.join(meeting.attendees)}\n"
            
            success_message += f"📧 Calendar invite sent to {user_email}\n"
            success_message += f"\n🔗 [View in Calendar]({meeting_url})"
            
            await send_message(chat_guid, success_message)
        else:
            await send_message(chat_guid, "❌ Failed to create the meeting. Please check your Google Calendar setup and try again.")
        
        # Reset conversation state
        conversation_manager.update_conversation(chat_guid, state=ConversationState.WAITING_FOR_COMMAND)
        
    except Exception as e:
        logger.error(f"Error processing meeting command for chat {chat_guid}: {e}")
        await send_message(chat_guid, "❌ Something went wrong while processing your meeting request. Please try again.")
        conversation_manager.update_conversation(chat_guid, state=ConversationState.WAITING_FOR_COMMAND)

async def process_email_response(chat_guid: str, message_text: str):
    """
    Process the user's email response and then continue with meeting creation.
    
    Args:
        chat_guid: The GUID of the chat
        message_text: The email address provided by the user
    """
    try:
        # Get conversation state
        conversation = conversation_manager.get_conversation(chat_guid)
        if not conversation or not conversation.last_command:
            await send_message(chat_guid, "❌ Sorry, I lost track of your meeting request. Please start over with `!schedule`")
            return
        
        # Validate email format
        email = message_text.strip()
        if not is_valid_email(email):
            await send_message(chat_guid, "❌ That doesn't look like a valid email address. Please try again:")
            return
        
        # Save email and continue with meeting processing
        conversation_manager.update_conversation(
            chat_guid,
            state=ConversationState.PROCESSING,
            user_email=email
        )
        
        await send_message(chat_guid, f"✅ Got it! I'll use {email} for your calendar invite.")
        
        # Now process the original meeting command
        await process_meeting_command(chat_guid, conversation.last_command, email)
        
    except Exception as e:
        logger.error(f"Error processing email response for chat {chat_guid}: {e}")
        await send_message(chat_guid, "❌ Something went wrong. Please try again with `!schedule`")
        conversation_manager.update_conversation(chat_guid, state=ConversationState.WAITING_FOR_COMMAND)

def is_valid_email(email: str) -> bool:
    """Validate email format using a simple regex."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

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
        
        logger.info(f"Sending message to {chat_guid}: {text[:50]}...")
        
        response = requests.post(
            url,
            json=data,
            params=params,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        response.raise_for_status()
        logger.info(f"Successfully sent message to {chat_guid}")
        
    except requests.RequestException as e:
        logger.error(f"Failed to send message to BlueBubbles: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error sending message: {e}")
        raise

@app.get("/stats")
async def get_stats():
    """Get bot statistics."""
    stats = conversation_manager.get_stats()
    
    # Add calendar stats if available
    if calendar_manager.service:
        try:
            upcoming_meetings = calendar_manager.list_upcoming_meetings(5)
            stats["upcoming_meetings_count"] = len(upcoming_meetings)
            stats["google_calendar_connected"] = True
        except:
            stats["google_calendar_connected"] = False
    else:
        stats["google_calendar_connected"] = False
    
    return stats

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG
    ) 