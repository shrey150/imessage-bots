# Custom API Endpoints

The iMessage Bot Framework provides full access to the underlying FastAPI application, allowing you to add custom REST API endpoints alongside your message handling functionality.

## Overview

Every bot includes a FastAPI application accessible via `bot.app`. This means you can:

- Add custom REST endpoints
- Implement webhooks for other services
- Create admin dashboards
- Build monitoring APIs
- Integrate with external systems

## Basic Usage

### Adding Simple Endpoints

```python
from imessage_bot_framework import Bot

bot = Bot("API Bot")

@bot.app.get("/hello")
async def hello_world():
    return {"message": "Hello, World!"}

@bot.app.get("/bot-info")
async def bot_info():
    return {
        "name": bot.name,
        "port": bot.port,
        "debug": bot.debug
    }
```

### POST Endpoints with Data

```python
from pydantic import BaseModel

class MessageRequest(BaseModel):
    text: str
    chat_guid: str

@bot.app.post("/send-message")
async def send_message(request: MessageRequest):
    success = bot.send_to_chat(request.text, request.chat_guid)
    return {
        "success": success,
        "message": "Message sent successfully" if success else "Failed to send message"
    }
```

## Advanced Patterns

### Authentication

```python
from fastapi import HTTPException, Depends, Header
from typing import Optional

# Simple API key authentication
async def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if x_api_key != "your-secret-api-key":
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

@bot.app.post("/admin/broadcast")
async def broadcast_message(
    request: MessageRequest,
    api_key: str = Depends(verify_api_key)
):
    # Only accessible with valid API key
    success = bot.send_to_chat(request.text, request.chat_guid)
    return {"success": success}
```

### Database Integration

```python
import sqlite3
from contextlib import asynccontextmanager

# Database setup
@bot.app.on_event("startup")
async def setup_database():
    conn = sqlite3.connect("bot_data.db")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY,
            text TEXT,
            sender TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.close()

@bot.app.get("/messages")
async def get_messages(limit: int = 50):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.execute(
        "SELECT * FROM messages ORDER BY timestamp DESC LIMIT ?",
        (limit,)
    )
    messages = [
        {"id": row[0], "text": row[1], "sender": row[2], "timestamp": row[3]}
        for row in cursor.fetchall()
    ]
    conn.close()
    return {"messages": messages}

# Store messages from bot handler
@bot.on_message
def log_message(message):
    conn = sqlite3.connect("bot_data.db")
    conn.execute(
        "INSERT INTO messages (text, sender) VALUES (?, ?)",
        (message.text, message.sender)
    )
    conn.commit()
    conn.close()
    return f"Logged: {message.text}"
```

### File Upload Endpoints

```python
from fastapi import File, UploadFile
import os

@bot.app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Save uploaded file
    file_path = f"uploads/{file.filename}"
    os.makedirs("uploads", exist_ok=True)
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    return {
        "filename": file.filename,
        "size": len(content),
        "path": file_path
    }
```

### WebSocket Support

```python
from fastapi import WebSocket, WebSocketDisconnect
import json

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@bot.app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Message: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Broadcast messages from bot to WebSocket clients
@bot.on_message
def broadcast_to_websockets(message):
    import asyncio
    asyncio.create_task(manager.broadcast(f"New message: {message.text}"))
    return None  # Don't send iMessage response
```

## Integration Examples

### Slack Integration

```python
import requests

@bot.app.post("/slack-webhook")
async def slack_webhook(data: dict):
    # Receive message from Slack
    slack_text = data.get("text", "")
    slack_user = data.get("user_name", "Slack User")
    
    # Forward to iMessage
    imessage_text = f"[Slack] {slack_user}: {slack_text}"
    chat_guid = "your-imessage-chat-guid"
    bot.send_to_chat(imessage_text, chat_guid)
    
    return {"status": "forwarded"}

@bot.on_message
def forward_to_slack(message):
    # Forward iMessage to Slack
    if not message.is_from_me:  # Don't forward your own messages
        slack_webhook_url = "your-slack-webhook-url"
        payload = {
            "text": f"[iMessage] {message.sender}: {message.text}"
        }
        requests.post(slack_webhook_url, json=payload)
    
    return None  # Don't send iMessage response
```

### GitHub Webhooks

```python
@bot.app.post("/github-webhook")
async def github_webhook(data: dict):
    event_type = data.get("action", "unknown")
    repo_name = data.get("repository", {}).get("name", "unknown")
    
    if event_type == "opened" and "pull_request" in data:
        pr = data["pull_request"]
        message = f"🔀 New PR opened in {repo_name}: {pr['title']}"
        bot.send_to_chat(message, "your-dev-team-chat-guid")
    
    elif event_type == "created" and "issue" in data:
        issue = data["issue"]
        message = f"🐛 New issue in {repo_name}: {issue['title']}"
        bot.send_to_chat(message, "your-dev-team-chat-guid")
    
    return {"status": "processed"}
```

### Monitoring Dashboard

```python
from fastapi.responses import HTMLResponse
import time

start_time = time.time()
message_count = 0

@bot.on_message
def count_messages(message):
    global message_count
    message_count += 1
    return None

@bot.app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    uptime = time.time() - start_time
    hours, remainder = divmod(uptime, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bot Dashboard</title>
        <meta http-equiv="refresh" content="30">
    </head>
    <body>
        <h1>Bot Dashboard</h1>
        <p><strong>Status:</strong> Running</p>
        <p><strong>Uptime:</strong> {int(hours)}h {int(minutes)}m {int(seconds)}s</p>
        <p><strong>Messages Processed:</strong> {message_count}</p>
        <p><strong>Port:</strong> {bot.port}</p>
        <p><strong>Debug Mode:</strong> {bot.debug}</p>
    </body>
    </html>
    """
    return html_content
```

## Security Best Practices

### Rate Limiting

```python
from fastapi import HTTPException
import time
from collections import defaultdict

# Simple rate limiter
rate_limit_storage = defaultdict(list)

def rate_limit(max_requests: int = 10, window_seconds: int = 60):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get client IP (simplified)
            client_ip = "127.0.0.1"  # In real implementation, extract from request
            
            now = time.time()
            # Clean old requests
            rate_limit_storage[client_ip] = [
                req_time for req_time in rate_limit_storage[client_ip]
                if now - req_time < window_seconds
            ]
            
            # Check rate limit
            if len(rate_limit_storage[client_ip]) >= max_requests:
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            
            # Record this request
            rate_limit_storage[client_ip].append(now)
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

@bot.app.get("/limited-endpoint")
@rate_limit(max_requests=5, window_seconds=60)
async def limited_endpoint():
    return {"message": "This endpoint is rate limited"}
```

### Input Validation

```python
from pydantic import BaseModel, validator
from typing import Optional

class ChatMessage(BaseModel):
    text: str
    chat_guid: str
    priority: Optional[str] = "normal"
    
    @validator('text')
    def text_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Message text cannot be empty')
        if len(v) > 1000:
            raise ValueError('Message text too long')
        return v
    
    @validator('priority')
    def priority_must_be_valid(cls, v):
        if v not in ['low', 'normal', 'high']:
            raise ValueError('Priority must be low, normal, or high')
        return v

@bot.app.post("/secure-send")
async def secure_send(message: ChatMessage):
    success = bot.send_to_chat(message.text, message.chat_guid)
    return {"success": success}
```

## Testing Endpoints

### Unit Testing

```python
from fastapi.testclient import TestClient

def test_custom_endpoints():
    client = TestClient(bot.app)
    
    # Test GET endpoint
    response = client.get("/bot-info")
    assert response.status_code == 200
    assert response.json()["name"] == bot.name
    
    # Test POST endpoint
    response = client.post("/send-message", json={
        "text": "Test message",
        "chat_guid": "test-guid"
    })
    assert response.status_code == 200
```

### Manual Testing

```bash
# Test with curl
curl http://localhost:8000/bot-info

# Test POST endpoint
curl -X POST http://localhost:8000/send-message \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello!", "chat_guid": "your-chat-guid"}'

# Test with authentication
curl -X POST http://localhost:8000/admin/broadcast \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key" \
  -d '{"text": "Admin message", "chat_guid": "chat-guid"}'
```

## Best Practices

### 1. Organize Endpoints

```python
# Create separate modules for different endpoint groups
from api.admin import admin_router
from api.webhooks import webhook_router

bot.app.include_router(admin_router, prefix="/admin")
bot.app.include_router(webhook_router, prefix="/webhooks")
```

### 2. Use Environment Variables

```python
import os

API_KEY = os.getenv("API_KEY", "default-dev-key")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
```

### 3. Add Comprehensive Logging

```python
import logging

logger = logging.getLogger(__name__)

@bot.app.post("/important-endpoint")
async def important_endpoint(data: dict):
    logger.info(f"Important endpoint called with data: {data}")
    try:
        result = process_data(data)
        logger.info(f"Successfully processed: {result}")
        return {"result": result}
    except Exception as e:
        logger.error(f"Error processing data: {e}")
        raise HTTPException(status_code=500, detail="Processing failed")
```

### 4. Document Your APIs

```python
@bot.app.post(
    "/send-message",
    summary="Send iMessage",
    description="Send a message to a specific iMessage chat",
    response_description="Success status and message"
)
async def send_message(request: MessageRequest):
    """
    Send a message to an iMessage chat.
    
    - **text**: The message content to send
    - **chat_guid**: The target chat GUID
    """
    success = bot.send_to_chat(request.text, request.chat_guid)
    return {"success": success}

# FastAPI automatically generates OpenAPI docs at /docs
```

## See Also

- [Bot Class](../api-reference/bot-class.md) - Main Bot class documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/) - Complete FastAPI guide
- [Examples](../examples/) - Complete bot examples with custom endpoints 