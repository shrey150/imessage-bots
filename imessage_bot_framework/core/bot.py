"""Main Bot class for the iMessage Bot Framework."""

import os
import logging
from typing import List, Callable, Dict, Any, Optional
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import uvicorn
from .message import Message

logger = logging.getLogger(__name__)


class WebhookData(BaseModel):
    """Pydantic model for webhook data validation."""
    type: str
    data: Dict[str, Any]


class Bot:
    """Main Bot class for creating iMessage bots."""
    
    def __init__(self, name: str = "Bot", port: int = 8000, debug: bool = False):
        """
        Initialize a Bot instance.
        
        Args:
            name: The bot's name
            port: Port to run the bot server on
            debug: Enable debug logging
        """
        self.name = name
        self.port = port
        self.debug = debug
        
        # Configure logging
        log_level = logging.DEBUG if debug else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Bot configuration from environment variables
        self.config = {
            "bluebubbles_url": os.getenv("BLUEBUBBLES_SERVER_URL", "http://localhost:1234"),
            "bluebubbles_password": os.getenv("BLUEBUBBLES_PASSWORD", ""),
        }
        
        # Message handlers and middleware
        self.message_handlers: List[Callable] = []
        self.middleware: List[Callable] = []
        
        # FastAPI app
        self.app = FastAPI(title=f"{self.name} Bot", version="1.0.0")
        self._setup_routes()
        
    def _setup_routes(self):
        """Set up FastAPI routes."""
        
        @self.app.get("/")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "bot_name": self.name,
                "version": "1.0.0"
            }
        
        @self.app.post("/webhook")
        async def handle_webhook(webhook_data: WebhookData, background_tasks: BackgroundTasks):
            """Handle incoming webhooks from BlueBubbles."""
            try:
                logger.debug(f"Received webhook: type={webhook_data.type}")
                
                # Only process message webhooks
                if webhook_data.type not in ["message", "updated-message", "new-message"]:
                    logger.debug(f"Ignoring webhook type: {webhook_data.type}")
                    return {"status": "ignored", "reason": "not a message"}
                
                # Extract message data
                message_data = webhook_data.data
                
                # Skip messages without text
                if not message_data.get("text"):
                    logger.debug("Ignoring message without text")
                    return {"status": "ignored", "reason": "no text content"}
                
                # Get chat GUID from different webhook types
                chat_guid = self._extract_chat_guid(webhook_data)
                if not chat_guid:
                    logger.debug("Could not extract chat GUID")
                    return {"status": "ignored", "reason": "no chat guid"}
                
                # Create Message object
                message = Message(
                    text=message_data.get("text", ""),
                    sender=self._extract_sender(message_data),
                    chat_guid=chat_guid,
                    raw_data=message_data,
                    bot_config=self.config
                )
                
                # Process message in background
                background_tasks.add_task(self._process_message, message)
                
                return {"status": "accepted"}
                
            except Exception as e:
                logger.error(f"Error handling webhook: {e}")
                return {"status": "error", "message": str(e)}
    
    def _extract_chat_guid(self, webhook_data: WebhookData) -> Optional[str]:
        """Extract chat GUID from webhook data."""
        message_data = webhook_data.data
        
        # Check for chats array first (new-message webhook)
        if message_data.get('chats'):
            chats = message_data.get('chats', [])
            if chats:
                return chats[0].get('guid')
        
        # Check for chat object (standard message webhook)
        if message_data.get('chat'):
            return message_data['chat'].get('guid')
        
        return None
    
    def _extract_sender(self, message_data: Dict[str, Any]) -> str:
        """Extract sender identifier from message data."""
        if message_data.get('isFromMe'):
            return "me"
        
        handle = message_data.get('handle', {})
        if isinstance(handle, dict):
            return handle.get('address', 'unknown')
        
        return 'unknown'
    
    async def _process_message(self, message: Message):
        """Process a message through all handlers and middleware."""
        try:
            logger.debug(f"Processing message: {message}")
            
            # Apply middleware
            for middleware_func in self.middleware:
                try:
                    result = middleware_func(message, self._run_handlers)
                    if result is not None:
                        # Middleware returned a response, send it
                        if isinstance(result, str):
                            message.reply(result)
                        return
                except Exception as e:
                    logger.error(f"Error in middleware {middleware_func.__name__}: {e}")
            
            # Run handlers if no middleware intercepted
            await self._run_handlers(message)
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    async def _run_handlers(self, message: Message):
        """Run all message handlers for a message."""
        for handler in self.message_handlers:
            try:
                result = handler(message)
                if result is not None:
                    # Handler returned a response, send it
                    if isinstance(result, str):
                        message.reply(result)
                    # Only first handler that returns something gets to respond
                    break
            except Exception as e:
                logger.error(f"Error in handler {handler.__name__}: {e}")
    
    def on_message(self, handler: Callable[[Message], Optional[str]]):
        """
        Register a message handler.
        
        Args:
            handler: Function that takes a Message and optionally returns a string response
            
        Returns:
            The handler function (for use as decorator)
        """
        self.message_handlers.append(handler)
        logger.info(f"Registered message handler: {handler.__name__}")
        return handler
    
    def use_middleware(self, middleware_func: Callable):
        """
        Register middleware.
        
        Args:
            middleware_func: Function that takes (message, next) and optionally returns a response
            
        Returns:
            The middleware function (for use as decorator)
        """
        self.middleware.append(middleware_func)
        logger.info(f"Registered middleware: {middleware_func.__name__}")
        return middleware_func
    
    def send_to_chat(self, text: str, chat_guid: str) -> bool:
        """
        Send a message to any chat.
        
        Args:
            text: The message text
            chat_guid: The chat GUID to send to
            
        Returns:
            True if message sent successfully, False otherwise
        """
        from .chat import Chat
        chat = Chat(chat_guid, self.config)
        return chat.send(text)
    
    def run(self, host: str = "127.0.0.1"):
        """
        Start the bot server.
        
        Args:
            host: Host to bind to
        """
        logger.info(f"Starting {self.name} on {host}:{self.port}")
        
        # Validate configuration
        if not self.config.get("bluebubbles_password"):
            logger.warning("BLUEBUBBLES_PASSWORD not set - bot may not work properly")
        
        # Start server
        uvicorn.run(
            self.app,
            host=host,
            port=self.port,
            log_level="debug" if self.debug else "info"
        ) 