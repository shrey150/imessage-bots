import asyncio
import logging
import requests
import uuid
from typing import Optional, List, Dict
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn

from config import config
from models import WebhookData
from feedback_ai import feedback_ai
from conversation_state import conversation_manager

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
    logger.info("Starting Feedback Bot...")
    try:
        config.validate()
        logger.info("Configuration validated successfully")
        logger.info(f"Monitoring {len(config.CHAT_GUIDS)} chat(s): {', '.join(config.CHAT_GUIDS[:3])}{'...' if len(config.CHAT_GUIDS) > 3 else ''}")
        logger.info(f"Cross-chat insights: {'enabled' if config.ENABLE_CROSS_CHAT_INSIGHTS else 'disabled'}")
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Feedback Bot...")

app = FastAPI(
    title="Feedback Bot",
    description="An intelligent feedback collection assistant for early-stage founders via iMessage",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def health_check():
    """Health check endpoint."""
    stats = conversation_manager.get_stats()
    ai_stats = feedback_ai.get_stats()
    return {
        "status": "ok",
        "message": f"Feedback Bot is running and ready to collect insights for {config.PRODUCT_NAME}!",
        "config": {
            "founder_name": config.FOUNDER_NAME,
            "product_name": config.PRODUCT_NAME,
            "monitored_chats": len(config.CHAT_GUIDS),
            "chat_guids": config.CHAT_GUIDS[:3] + ["..."] if len(config.CHAT_GUIDS) > 3 else config.CHAT_GUIDS,  # Show first 3 for privacy
            "max_questions_per_session": config.MAX_QUESTIONS_PER_SESSION,
            "cross_chat_insights_enabled": config.ENABLE_CROSS_CHAT_INSIGHTS
        },
        "conversation_stats": stats,
        "ai_stats": ai_stats
    }

@app.post("/webhook")
async def handle_webhook(webhook_data: WebhookData, background_tasks: BackgroundTasks):
    """
    Handle incoming webhooks from BlueBubbles for feedback collection across multiple chats.
    
    The bot analyzes feedback, asks Mom Test questions, and structures insights with cross-chat learning.
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
        logger.info(f"Monitored chats: {len(config.CHAT_GUIDS)}")
        logger.info(f"Message text: {message_text[:100]}...")
        
        # Check if this chat is in our monitored list
        if not config.is_monitored_chat(chat_guid):
            logger.info(f"Ignoring message from unmonitored chat: {chat_guid}")
            return {"status": "ignored", "reason": "chat not monitored"}
        
        logger.info(f"Processing feedback message from monitored chat: {message_text[:50]}...")
        
        # Process the feedback message in the background
        background_tasks.add_task(process_feedback_message, chat_guid, message_text)
        
        return {"status": "accepted", "message": "Processing your feedback!"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def send_message(chat_guid: str, text: str, method: str = "apple-script"):
    """
    Send a message using BlueBubbles API.
    
    Args:
        chat_guid: The chat GUID to send the message to
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

def parse_response_for_sending(response_text: str) -> List[str]:
    """
    Parse a response to determine if it should be sent as multiple messages.
    Only splits if there are distinct ideas separated by line breaks.
    
    Args:
        response_text: The full response text
        
    Returns:
        List of message parts (1-2 messages max)
    """
    # Check for intentional line breaks that indicate separate messages
    if '\n\n' in response_text:
        parts = [part.strip() for part in response_text.split('\n\n') if part.strip()]
        # Only return multiple parts if we have exactly 2 distinct ideas
        if len(parts) == 2 and all(len(part) > 10 for part in parts):
            return parts[:2]  # Cap at 2 messages max
    
    # Default: return as single message
    return [response_text]

async def send_multiple_messages(chat_guid: str, messages: List[str], method: str = "apple-script"):
    """
    Send multiple messages in sequence with natural delays to simulate real texting.
    Limited to at most 2 messages per response cycle.
    
    Args:
        chat_guid: The chat GUID to send the messages to
        messages: List of message texts to send (max 2)
        method: The method to use for sending (default: apple-script)
    """
    import random
    
    # Ensure we never send more than 2 messages
    messages = messages[:2]
    
    for i, message in enumerate(messages):
        if i > 0:  # Add delay between messages (except for the first one)
            # Natural typing delay based on message length
            base_delay = 0.5  # Minimum delay
            typing_delay = len(message) * 0.02  # ~20ms per character to simulate typing
            random_delay = random.uniform(0.2, 0.8)  # Random human variation
            
            total_delay = min(base_delay + typing_delay + random_delay, 3.0)  # Cap at 3 seconds
            await asyncio.sleep(total_delay)
        
        await send_message(chat_guid, message, method)
        logger.info(f"Sent message {i+1}/{len(messages)}: {message[:30]}...")

async def broadcast_cross_chat_probe(insight_theme: str, originating_chat_guid: str):
    """
    Send a cross-chat insight probe to other monitored chats (excluding the originating one).
    This helps diagnose issues across multiple conversations while preserving privacy.
    """
    if not config.ENABLE_CROSS_CHAT_INSIGHTS:
        return
    
    # Get all conversations except the originating one
    all_conversations = conversation_manager.get_all_conversations()
    target_chats = [
        chat_guid for chat_guid in all_conversations.keys() 
        if chat_guid != originating_chat_guid and chat_guid in config.CHAT_GUIDS
    ]
    
    if not target_chats:
        return
    
    logger.info(f"Broadcasting cross-chat probe for theme '{insight_theme}' to {len(target_chats)} chats")
    
    # Generate cross-chat probes for each target chat
    probe_tasks = []
    for target_chat_guid in target_chats:
        probe = conversation_manager.get_cross_chat_probe(target_chat_guid)
        if probe:
            probe_tasks.append(send_message(target_chat_guid, probe))
            logger.info(f"Scheduling cross-chat probe for {target_chat_guid}: {probe[:50]}...")
    
    # Send probes concurrently to all target chats
    if probe_tasks:
        await asyncio.gather(*probe_tasks, return_exceptions=True)

async def process_feedback_message(chat_guid: str, message_text: str):
    """
    Process an incoming feedback message and generate appropriate response.
    
    Args:
        chat_guid: The GUID of the chat
        message_text: The text content of the message
    """
    try:
        # Process the message and extract feedback
        conversation = conversation_manager.process_user_message(chat_guid, message_text)
        logger.info(f"Processing feedback for conversation state: {conversation.state}")
        
        # Check if session is ending BEFORE we process the response
        session_was_ending = conversation_manager.is_session_ending(conversation)
        previous_state = conversation.state
        
        # Get comprehensive conversation context for AI
        context = conversation_manager.get_conversation_context(chat_guid)
        
        # Check if we should trigger cross-chat probes based on new insights
        if (conversation.current_feedback and 
            config.ENABLE_CROSS_CHAT_INSIGHTS and 
            conversation.total_feedback_collected > 0):
            
            # Schedule cross-chat probe broadcast (non-blocking)
            asyncio.create_task(broadcast_cross_chat_probe(
                conversation.current_feedback.feedback_type.value, 
                chat_guid
            ))
        
        # Determine response strategy and generate response (single message preferred)
        if conversation.state.value == "initial_contact" and conversation.total_feedback_collected == 0:
            # First interaction - welcome and encourage feedback
            response_text = await feedback_ai.generate_welcome_message()
        elif context.get("cross_chat_probe"):
            # Use cross-chat insight probe
            response_text = context["cross_chat_probe"]
            logger.info(f"Using cross-chat probe: {context['cross_chat_probe'][:50]}...")
        elif conversation_manager.should_probe_deeper(conversation):
            # Use GPT-4o to generate contextual Mom Test probe question
            if conversation.current_feedback:
                response_text = await feedback_ai.generate_mom_test_probe(
                    conversation.current_feedback.feedback_type, 
                    message_text
                )
            else:
                # Fallback if no current feedback available
                response_text = await feedback_ai.generate_response(message_text, context)
        elif conversation_manager.should_summarize(conversation):
            # Summarize feedback collected so far
            conversation.state = conversation.state.SUMMARIZING
            response_text = await feedback_ai.generate_response(message_text, context)
        else:
            # Generate contextually appropriate response with full conversation context
            response_text = await feedback_ai.generate_response(message_text, context)
        
        # Parse response for potential line breaks (split only if absolutely necessary)
        response_parts = parse_response_for_sending(response_text)
        
        # Send the response (single message or at most 2 if distinct ideas)
        if len(response_parts) == 1:
            await send_message(chat_guid, response_parts[0])
        else:
            await send_multiple_messages(chat_guid, response_parts)
        
        # Mark messages as sent in conversation manager
        for response_part in response_parts:
            conversation_manager.mark_message_sent(chat_guid, response_part)
        
        logger.info(f"Sent {len(response_parts)} message(s) for feedback in chat {chat_guid}")
        
        # Check if session is ending AFTER we've sent the response
        session_is_ending = conversation_manager.is_session_ending(conversation)
        created_issues = []  # Initialize to avoid NameError
        
        # Auto-trigger Linear issue creation if session is ending and Linear is enabled
        if (session_is_ending and config.ENABLE_LINEAR_INTEGRATION and 
            config.AUTO_TRIAGE_ON_SESSION_END and conversation.total_feedback_collected > 0):
            
            # Check if we haven't already triaged this session
            if not hasattr(conversation, '_triaged_to_linear') or not conversation._triaged_to_linear:
                logger.info(f"🎯 Feedback session ending for chat {chat_guid} - triggering automatic Linear triaging")
                logger.info(f"   Previous state: {previous_state}")
                logger.info(f"   Current state: {conversation.state}")
                logger.info(f"   Total feedback collected: {conversation.total_feedback_collected}")
                logger.info(f"   Questions asked: {conversation.total_questions_asked}")
                
                # Schedule Linear triaging in background
                asyncio.create_task(auto_triage_session_to_linear(chat_guid))
            else:
                logger.info(f"⏭️  Session for chat {chat_guid} already triaged to Linear, skipping")
        
        # Optional: Send a notification back to the chat
        if config.NOTIFY_USER_ON_TRIAGE and created_issues:
            await send_feedback_processed_notification(chat_guid, created_issues)
        
    except Exception as e:
        logger.error(f"Error processing feedback message for chat {chat_guid}: {e}")
        # Send a helpful error message
        fallback = "Thanks for your message! I'm having a small technical issue, but I'd still love to hear your feedback. Could you try sending it again?"
        await send_message(chat_guid, fallback)

async def auto_triage_session_to_linear(chat_guid: str):
    """Background task to automatically triage a completed feedback session to Linear."""
    try:
        logger.info(f"🚀 Starting automatic Linear triaging for chat session: {chat_guid}")
        
        # Import here to avoid circular imports
        from linear_integration import feedback_triager
        
        # Collect feedback from this specific chat
        chat_feedback_data = conversation_manager.collect_feedback_for_chat(chat_guid)
        
        if not chat_feedback_data["feedback_items"]:
            logger.info(f"⏭️  No feedback items found for chat session {chat_guid}, skipping Linear triaging")
            return
        
        logger.info(f"📊 Chat session {chat_guid} feedback summary:")
        logger.info(f"   Total feedback items: {chat_feedback_data['total_feedback']}")
        logger.info(f"   Session state: {chat_feedback_data['session_state']}")
        logger.info(f"   Questions asked: {chat_feedback_data['total_questions_asked']}")
        
        # Get relevant cross-chat insights for context
        all_insights = conversation_manager._global_state.cross_chat_insights
        relevant_insights = {}
        
        # Only include insights that might be relevant to this session's feedback
        for item in chat_feedback_data["feedback_items"]:
            feedback_type = item["feedback"].feedback_type
            for theme, insight in all_insights.items():
                if insight.feedback_type == feedback_type and insight.frequency_count > 1:
                    relevant_insights[theme] = insight
        
        if relevant_insights:
            logger.info(f"🔗 Found {len(relevant_insights)} relevant cross-chat insights for session {chat_guid}")
        
        # Triage this session's feedback to Linear
        created_issues = await feedback_triager.triage_chat_session_to_linear(
            chat_feedback_data, 
            relevant_insights
        )
        
        if created_issues:
            # Mark session as triaged
            conversation_manager.mark_session_triaged(chat_guid)
            
            logger.info(f"🎉 Auto-triaging completed for chat session {chat_guid}")
            logger.info(f"   Created {len(created_issues)} Linear issues:")
            
            for issue in created_issues:
                linear_issue = issue["linear_issue"]
                session_context = issue.get("session_context", {})
                
                logger.info(f"   ✅ {linear_issue['identifier']}: {linear_issue['title']}")
                logger.info(f"      URL: {linear_issue['url']}")
                logger.info(f"      Session questions: {session_context.get('questions_asked', 0)}")
                logger.info(f"      Feedback items: {session_context.get('feedback_count', 0)}")
            
            # Optional: Send a notification back to the chat
            if config.NOTIFY_USER_ON_TRIAGE:
                await send_feedback_processed_notification(chat_guid, created_issues)
            
        else:
            logger.warning(f"⚠️  Auto-triaging for chat session {chat_guid} completed but no Linear issues were created")
        
    except Exception as e:
        logger.error(f"❌ Error in auto-triaging for chat session {chat_guid}: {e}")

async def send_feedback_processed_notification(chat_guid: str, created_issues: List[Dict]):
    """
    Optional: Send a notification to the user that their feedback was processed.
    This is commented out by default to avoid spam, but can be enabled if desired.
    """
    try:
        if len(created_issues) == 1:
            issue = created_issues[0]["linear_issue"]
            message = f"Thanks for all your feedback! I've created an issue to track it: {issue['identifier']} 🎯"
        else:
            message = f"Thanks for all your feedback! I've created {len(created_issues)} issues to track the different points you raised 🎯"
        
        await send_message(chat_guid, message)
        logger.info(f"📨 Sent feedback processed notification to chat {chat_guid}")
        
    except Exception as e:
        logger.error(f"Error sending feedback processed notification to chat {chat_guid}: {e}")

@app.get("/stats")
async def get_stats():
    """Get feedback collection statistics across all monitored chats."""
    conversation_stats = conversation_manager.get_stats()
    ai_stats = feedback_ai.get_stats()
    
    return {
        "feedback_collection": conversation_stats,
        "ai_performance": ai_stats,
        "summary": {
            "total_conversations": conversation_stats.get("total_conversations", 0),
            "total_feedback_items": conversation_stats.get("total_feedback_items", 0),
            "active_conversations": conversation_stats.get("active_conversations", 0),
            "monitored_chats": conversation_stats.get("monitored_chats", 0),
            "cross_chat_insights": len(conversation_stats.get("cross_chat_insights", {})),
            "most_common_feedback": max(
                conversation_stats.get("feedback_by_type", {}).items(), 
                key=lambda x: x[1], 
                default=("none", 0)
            )[0] if conversation_stats.get("feedback_by_type") else "none"
        }
    }

@app.get("/cross-chat-insights")
async def get_cross_chat_insights():
    """Get cross-chat insights without revealing private information."""
    stats = conversation_manager.get_stats()
    insights = stats.get("cross_chat_insights", {})
    
    return {
        "insights": insights,
        "summary": {
            "total_insights": len(insights),
            "high_severity_count": len([i for i in insights.values() if i.get("severity") == "high"]),
            "themes": list(insights.keys())
        }
    }

@app.get("/feedback-summary")
async def get_feedback_summary():
    """Get a summary of all feedback collected across conversations."""
    all_conversations = conversation_manager.get_all_conversations()
    
    summary = {
        "total_conversations": len(all_conversations),
        "feedback_by_type": {},
        "recent_feedback": []
    }
    
    for conversation in all_conversations.values():
        for message in conversation.conversation_history:
            if message.role == "user" and message.feedback_type:
                feedback_type = message.feedback_type.value
                summary["feedback_by_type"][feedback_type] = summary["feedback_by_type"].get(feedback_type, 0) + 1
                
                if len(summary["recent_feedback"]) < 10:
                    summary["recent_feedback"].append({
                        "type": feedback_type,
                        "content": message.content[:100] + "..." if len(message.content) > 100 else message.content,
                        "timestamp": message.timestamp.isoformat()
                    })
    
    return summary

@app.post("/triage-to-linear")
async def triage_feedback_to_linear(background_tasks: BackgroundTasks):
    """
    Triage all collected feedback into Linear issues.
    
    This endpoint collects all feedback from conversations, uses GPT-4o to format it,
    and creates issues in Linear.
    """
    try:
        # Check if Linear integration is enabled
        if not config.ENABLE_LINEAR_INTEGRATION:
            raise HTTPException(
                status_code=400, 
                detail="Linear integration is disabled. Set ENABLE_LINEAR_INTEGRATION=true to enable."
            )
        
        # Collect all feedback for triaging
        logger.info("Collecting feedback for Linear triaging...")
        feedback_data = conversation_manager.collect_all_feedback_for_triaging()
        
        if not feedback_data["feedback_items"]:
            return {
                "status": "no_feedback",
                "message": "No feedback available to triage",
                "total_conversations": feedback_data["total_conversations"]
            }
        
        logger.info(f"Found {len(feedback_data['feedback_items'])} feedback items to triage")
        
        # Process triaging in background
        background_tasks.add_task(
            process_linear_triaging, 
            feedback_data["feedback_items"], 
            feedback_data["cross_chat_insights"]
        )
        
        return {
            "status": "processing",
            "message": f"Triaging {len(feedback_data['feedback_items'])} feedback items to Linear",
            "feedback_count": len(feedback_data["feedback_items"]),
            "total_conversations": feedback_data["total_conversations"],
            "cross_chat_insights": len(feedback_data["cross_chat_insights"])
        }
        
    except Exception as e:
        logger.error(f"Error initiating Linear triaging: {e}")
        raise HTTPException(status_code=500, detail=f"Error initiating triaging: {str(e)}")

@app.get("/linear-status")
async def get_linear_status():
    """Check Linear integration status and configuration."""
    try:
        if not config.ENABLE_LINEAR_INTEGRATION:
            return {
                "status": "disabled",
                "message": "Linear integration is disabled"
            }
        
        # Import here to avoid issues if Linear isn't configured
        from linear_integration import feedback_triager
        
        # Try to get teams to test connection
        teams = await feedback_triager.linear_client.get_teams()
        team_id = await feedback_triager.linear_client.get_team_id()
        
        return {
            "status": "enabled",
            "connection": "success" if teams else "failed",
            "teams_found": len(teams),
            "configured_team": config.LINEAR_TEAM_KEY,
            "target_team_id": team_id,
            "api_configured": bool(config.LINEAR_API_KEY)
        }
        
    except Exception as e:
        logger.error(f"Error checking Linear status: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

async def process_linear_triaging(feedback_items, cross_chat_insights):
    """Background task to process Linear triaging."""
    try:
        from linear_integration import feedback_triager
        
        logger.info(f"Starting Linear triaging for {len(feedback_items)} feedback items")
        
        # Triage feedback to Linear
        created_issues = await feedback_triager.triage_feedback_to_linear(
            feedback_items, 
            cross_chat_insights
        )
        
        logger.info(f"Linear triaging completed. Created {len(created_issues)} issues:")
        for issue in created_issues:
            linear_issue = issue["linear_issue"]
            logger.info(f"  - {linear_issue['identifier']}: {linear_issue['title']}")
            logger.info(f"    URL: {linear_issue['url']}")
        
        # Optionally clear triaged feedback (commented out to preserve history)
        # conversation_manager.clear_triaged_feedback()
        
    except Exception as e:
        logger.error(f"Error in Linear triaging background task: {e}")

@app.get("/conversation/{chat_guid}")
async def get_conversation_info(chat_guid: str):
    """Get information about a specific conversation."""
    conversation = conversation_manager.get_conversation(chat_guid)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {
        "chat_guid": chat_guid,
        "state": conversation.state.value,
        "total_feedback_collected": conversation.total_feedback_collected,
        "total_questions_asked": conversation.total_questions_asked,
        "user_profile": {
            "engagement_level": conversation.user_profile.engagement_level,
            "total_feedback_items": conversation.user_profile.total_feedback_items,
            "feedback_types": conversation.user_profile.feedback_types
        },
        "conversation_length": len(conversation.conversation_history),
        "last_interaction": conversation.last_interaction.isoformat(),
        "current_feedback": {
            "type": conversation.current_feedback.feedback_type.value,
            "summary": conversation.current_feedback.summary
        } if conversation.current_feedback else None
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.HOST,
        port=config.PORT,
        reload=config.DEBUG,
        log_level="info" if config.DEBUG else "warning"
    ) 