# Bot Class

The `Bot` class is the core component of the iMessage Bot Framework. It handles webhook processing, message routing, and provides a FastAPI web server.

## Constructor

### `Bot(name, port=8000, debug=False)`

Creates a new Bot instance.

**Parameters:**
- `name` (str): The bot's name (used in logging and API responses)
- `port` (int, optional): Port for the web server. Default: 8000
- `debug` (bool, optional): Enable debug logging. Default: False

**Example:**
```python
from imessage_bot_framework import Bot

# Basic bot
bot = Bot("My Bot")

# Bot with custom port and debug enabled
bot = Bot("Debug Bot", port=8080, debug=True)
```

## Properties

### `app`
FastAPI application instance. Use this to add custom endpoints, middleware, or configure the web server.

**Type:** `FastAPI`

**Example:**
```python
# Add custom endpoint
@bot.app.get("/custom")
async def custom_endpoint():
    return {"message": "Hello from custom endpoint!"}

# Add middleware
@bot.app.middleware("http")
async def add_cors_header(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response
```

### `config`
Bot configuration dictionary containing BlueBubbles server settings.

**Type:** `Dict[str, Any]`

**Properties:**
- `bluebubbles_url`: BlueBubbles server URL
- `bluebubbles_password`: Server password

**Example:**
```python
print(f"Server URL: {bot.config['bluebubbles_url']}")
print(f"Password set: {'Yes' if bot.config['bluebubbles_password'] else 'No'}")
```

### `name`
The bot's name.

**Type:** `str`

### `port`
The port the web server runs on.

**Type:** `int`

### `debug`
Whether debug mode is enabled.

**Type:** `bool`

## Methods

### `on_message(handler)`

Decorator to register a message handler function.

**Parameters:**
- `handler` (Callable[[Message], Optional[str]]): Function that processes messages

**Returns:** The handler function (for decorator chaining)

**Handler Function Signature:**
```python
def handler(message: Message) -> Optional[str]:
    # Process message
    # Return string to send response, or None for no response
```

**Example:**
```python
@bot.on_message
def handle_all_messages(message):
    return f"You said: {message.text}"

@bot.on_message
def handle_specific(message):
    if message.text == "ping":
        return "pong!"
    return None  # Let other handlers process this message
```

### `use_middleware(middleware_func)`

Register middleware for message processing.

**Parameters:**
- `middleware_func` (Callable): Middleware function

**Middleware Function Signature:**
```python
def middleware(message: Message, next: Callable) -> Optional[str]:
    # Pre-processing
    result = next(message)  # Call next middleware/handlers
    # Post-processing
    return result
```

**Example:**
```python
@bot.use_middleware
def logging_middleware(message, next):
    print(f"Processing: {message.text}")
    result = next(message)
    print(f"Response: {result}")
    return result
```

### `send_to_chat(text, chat_guid)`

Send a message to a specific chat.

**Parameters:**
- `text` (str): Message text to send
- `chat_guid` (str): Target chat GUID

**Returns:** `bool` - True if message sent successfully, False otherwise

**Example:**
```python
# Send to specific chat
success = bot.send_to_chat("Hello!", "iMessage;-;+1234567890")

# Send with error handling
if not bot.send_to_chat("Important message", chat_guid):
    print("Failed to send message")
```

### `run(host="127.0.0.1")`

Start the bot server.

**Parameters:**
- `host` (str, optional): Host to bind to. Default: "127.0.0.1"

**Example:**
```python
# Run locally
bot.run()

# Run on all interfaces
bot.run(host="0.0.0.0")

# This is blocking - put at end of script
if __name__ == "__main__":
    bot.run()
```

## Built-in Endpoints

The Bot automatically creates these endpoints:

### `GET /`
Health check endpoint.

**Response:**
```json
{
    "status": "healthy",
    "bot_name": "Your Bot Name",
    "version": "1.0.0"
}
```

### `POST /webhook`
BlueBubbles webhook endpoint. Automatically processes incoming messages.

**Request Body:**
```json
{
    "type": "message",
    "data": {
        "text": "Message content",
        "isFromMe": false,
        "chat": {"guid": "chat-guid"},
        ...
    }
}
```

## Configuration

The Bot reads configuration from environment variables:

```bash
# Required
BLUEBUBBLES_SERVER_URL=http://localhost:1234
BLUEBUBBLES_PASSWORD=your-server-password

# Optional
DEBUG=true
```

## Advanced Usage

### Multiple Message Handlers

```python
@bot.on_message
def first_handler(message):
    if message.text == "special":
        return "Handled by first handler"
    return None  # Pass to next handler

@bot.on_message
def second_handler(message):
    return f"Handled by second handler: {message.text}"
```

Handlers are called in registration order. First handler to return a non-None value wins.

### Custom FastAPI Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

# Add CORS
bot.app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom static files
from fastapi.staticfiles import StaticFiles
bot.app.mount("/static", StaticFiles(directory="static"), name="static")
```

### Error Handling

```python
@bot.on_message
def safe_handler(message):
    try:
        # Your bot logic here
        result = process_message(message.text)
        return f"Result: {result}"
    except Exception as e:
        # Log error
        print(f"Error processing message: {e}")
        return "Sorry, something went wrong!"
```

### Async Message Handlers

```python
import asyncio

@bot.on_message
def async_handler(message):
    if message.text.startswith("async "):
        # Run async function in background
        asyncio.create_task(process_async_message(message))
        return "Processing your request..."
    return None

async def process_async_message(message):
    # Do async work
    await asyncio.sleep(2)
    
    # Send delayed response
    bot.send_to_chat("Async processing complete!", message.chat_guid)
```

## Event Hooks

The Bot supports various lifecycle hooks:

```python
@bot.app.on_event("startup")
async def startup_event():
    print("Bot is starting up...")
    # Initialize databases, load models, etc.

@bot.app.on_event("shutdown")
async def shutdown_event():
    print("Bot is shutting down...")
    # Cleanup resources
```

## Examples

### Basic Echo Bot

```python
from imessage_bot_framework import Bot

bot = Bot("Echo Bot")

@bot.on_message
def echo(message):
    return f"Echo: {message.text}"

bot.run()
```

### Command Bot with Admin Features

```python
from imessage_bot_framework import Bot
from imessage_bot_framework.decorators import only_from_me

bot = Bot("Command Bot")

@bot.on_message
def commands(message):
    if message.text == "ping":
        return "pong!"
    elif message.text == "time":
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
    return None

@bot.on_message
@only_from_me()
def admin(message):
    if message.text == "!status":
        return "Bot is running!"
    return None

bot.run()
```

### Bot with Custom API

```python
from imessage_bot_framework import Bot
from pydantic import BaseModel

bot = Bot("API Bot")

class MessageRequest(BaseModel):
    text: str
    chat_guid: str

@bot.app.post("/api/send")
async def send_message(request: MessageRequest):
    success = bot.send_to_chat(request.text, request.chat_guid)
    return {"success": success}

@bot.on_message
def handle_message(message):
    return f"Received: {message.text}"

bot.run()
```

## See Also

- [Message Class](message-class.md) - Working with message objects
- [Chat Class](chat-class.md) - Chat interaction methods
- [Decorators](decorators.md) - Message filtering decorators
- [Examples](../examples/) - Complete bot examples 