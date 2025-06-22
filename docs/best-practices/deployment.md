# Deployment

This guide covers best practices for deploying iMessage bots built with the framework to production environments.

## Production Checklist

Before deploying your bot to production:

- [ ] **Environment variables** configured and secured
- [ ] **BlueBubbles server** running and accessible
- [ ] **Error handling** implemented
- [ ] **Logging** configured for monitoring
- [ ] **Health checks** enabled
- [ ] **Process management** set up
- [ ] **SSL/TLS** configured (if needed)
- [ ] **Backup strategy** in place

## Environment Configuration

### Production Environment Variables

```bash
# .env.production
# Server Configuration
BLUEBUBBLES_SERVER_URL=http://localhost:1234
BLUEBUBBLES_PASSWORD=your-secure-production-password

# Bot Configuration
BOT_NAME=Production Bot
DEBUG=false
LOG_LEVEL=INFO

# Security
API_KEY=your-secure-api-key
JWT_SECRET=your-jwt-secret

# Monitoring
SENTRY_DSN=your-sentry-dsn
METRICS_ENABLED=true

# Performance
WORKER_PROCESSES=2
MAX_MESSAGE_SIZE=1048576
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

### Configuration Management

```python
# config/production.py
import os
from typing import Optional

class ProductionConfig:
    """Production configuration settings."""
    
    # Server
    BLUEBUBBLES_SERVER_URL = os.getenv("BLUEBUBBLES_SERVER_URL")
    BLUEBUBBLES_PASSWORD = os.getenv("BLUEBUBBLES_PASSWORD")
    
    # Security
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.getenv("SECRET_KEY")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "/var/log/bot.log")
    
    # Performance
    WORKERS = int(os.getenv("WORKER_PROCESSES", "2"))
    TIMEOUT = int(os.getenv("TIMEOUT", "30"))
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration."""
        required = [
            "BLUEBUBBLES_SERVER_URL",
            "BLUEBUBBLES_PASSWORD",
            "SECRET_KEY"
        ]
        return all(getattr(cls, var) for var in required)

# Validate configuration on import
if not ProductionConfig.validate():
    raise RuntimeError("Missing required production configuration")
```

## Process Management

### Using systemd (Linux)

Create a systemd service file:

```ini
# /etc/systemd/system/imessage-bot.service
[Unit]
Description=iMessage Bot Service
After=network.target

[Service]
Type=simple
User=bot
Group=bot
WorkingDirectory=/opt/imessage-bot
Environment=PATH=/opt/imessage-bot/venv/bin
ExecStart=/opt/imessage-bot/venv/bin/python main.py
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=imessage-bot

# Security
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ReadWritePaths=/opt/imessage-bot/logs

[Install]
WantedBy=multi-user.target
```

Manage the service:
```bash
# Install and start service
sudo systemctl daemon-reload
sudo systemctl enable imessage-bot
sudo systemctl start imessage-bot

# Check status
sudo systemctl status imessage-bot

# View logs
sudo journalctl -u imessage-bot -f
```

### Using Docker

Create a production Dockerfile:

```dockerfile
# Dockerfile
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user
RUN groupadd -r bot && useradd -r -g bot bot

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=bot:bot . .

# Create logs directory
RUN mkdir -p /app/logs && chown bot:bot /app/logs

# Switch to non-root user
USER bot

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "main.py"]
```

Docker Compose for production:

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  bot:
    build: .
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - BLUEBUBBLES_SERVER_URL=${BLUEBUBBLES_SERVER_URL}
      - BLUEBUBBLES_PASSWORD=${BLUEBUBBLES_PASSWORD}
      - DEBUG=false
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 10s
      retries: 3
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Optional: Add reverse proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on:
      - bot
    restart: unless-stopped
```

Deploy with Docker:
```bash
# Build and start
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f bot
```

## Logging and Monitoring

### Production Logging

```python
# logging_config.py
import logging
import logging.handlers
import os
from datetime import datetime

def setup_production_logging(
    log_level: str = "INFO",
    log_file: str = "/var/log/bot.log",
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5
):
    """Set up production logging configuration."""
    
    # Create logs directory
    log_dir = os.path.dirname(log_file)
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            # Rotating file handler
            logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count
            ),
            # Console handler for systemd
            logging.StreamHandler()
        ]
    )
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

# In your main.py
from config.production import ProductionConfig
from logging_config import setup_production_logging

if not ProductionConfig.DEBUG:
    setup_production_logging(
        log_level=ProductionConfig.LOG_LEVEL,
        log_file=ProductionConfig.LOG_FILE
    )
```

### Health Monitoring

```python
# health.py
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

class HealthMonitor:
    """Monitor bot health and performance."""
    
    def __init__(self):
        self.start_time = time.time()
        self.message_count = 0
        self.error_count = 0
        self.last_message_time = None
        self.bluebubbles_status = "unknown"
    
    def record_message(self):
        """Record a processed message."""
        self.message_count += 1
        self.last_message_time = datetime.now()
    
    def record_error(self):
        """Record an error."""
        self.error_count += 1
    
    async def check_bluebubbles(self, bot) -> bool:
        """Check BlueBubbles server connectivity."""
        try:
            # Test BlueBubbles connection
            import httpx
            url = f"{bot.config['bluebubbles_url']}/api/v1/ping"
            params = {"password": bot.config['bluebubbles_password']}
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url, params=params)
                self.bluebubbles_status = "healthy" if response.status_code == 200 else "unhealthy"
                return response.status_code == 200
        except Exception:
            self.bluebubbles_status = "unreachable"
            return False
    
    def get_health_report(self) -> Dict[str, Any]:
        """Get comprehensive health report."""
        uptime = time.time() - self.start_time
        
        return {
            "status": "healthy",
            "uptime_seconds": uptime,
            "uptime_formatted": str(timedelta(seconds=int(uptime))),
            "messages_processed": self.message_count,
            "errors": self.error_count,
            "error_rate": self.error_count / max(self.message_count, 1),
            "last_message": self.last_message_time.isoformat() if self.last_message_time else None,
            "bluebubbles_status": self.bluebubbles_status,
            "timestamp": datetime.now().isoformat()
        }

# Add to your bot
health_monitor = HealthMonitor()

@bot.app.get("/health")
async def health_check():
    """Health check endpoint for load balancers."""
    await health_monitor.check_bluebubbles(bot)
    return health_monitor.get_health_report()

@bot.on_message
def monitor_messages(message):
    health_monitor.record_message()
    return None  # Let other handlers process
```

### Error Tracking with Sentry

```python
# sentry_config.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
import os

def setup_sentry():
    """Configure Sentry for error tracking."""
    sentry_dsn = os.getenv("SENTRY_DSN")
    
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[
                FastApiIntegration(auto_enable=True),
                LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)
            ],
            traces_sample_rate=0.1,  # Performance monitoring
            environment=os.getenv("ENVIRONMENT", "production"),
            release=os.getenv("BOT_VERSION", "1.0.0")
        )

# Add error handling to message handlers
@bot.on_message
def safe_message_handler(message):
    try:
        # Your bot logic here
        return process_message(message)
    except Exception as e:
        # Sentry will automatically capture this
        logger.error(f"Error processing message: {e}", exc_info=True)
        return "Sorry, something went wrong. The error has been reported."
```

## Security Best Practices

### API Security

```python
# security.py
from fastapi import HTTPException, Depends, Header
from typing import Optional
import hmac
import hashlib
import os

def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Verify API key for admin endpoints."""
    expected_key = os.getenv("API_KEY")
    
    if not expected_key:
        raise HTTPException(status_code=500, detail="API key not configured")
    
    if not x_api_key or not hmac.compare_digest(x_api_key, expected_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return x_api_key

def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str
) -> bool:
    """Verify webhook signature for security."""
    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"sha256={expected_signature}", signature)

# Secure admin endpoints
@bot.app.post("/admin/send")
async def admin_send_message(
    request: MessageRequest,
    api_key: str = Depends(verify_api_key)
):
    success = bot.send_to_chat(request.text, request.chat_guid)
    return {"success": success}
```

### Rate Limiting

```python
# rate_limiting.py
from fastapi import HTTPException, Request
import time
from collections import defaultdict
from typing import Dict, List

class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = defaultdict(list)
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is within rate limit."""
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > window_start
        ]
        
        # Check limit
        if len(self.requests[identifier]) >= self.max_requests:
            return False
        
        # Record this request
        self.requests[identifier].append(now)
        return True

# Global rate limiter
rate_limiter = RateLimiter(max_requests=100, window_seconds=60)

@bot.app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting to all requests."""
    client_ip = request.client.host
    
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    response = await call_next(request)
    return response
```

## Performance Optimization

### Production Bot Template

```python
# production_bot.py
import asyncio
import logging
import os
import signal
import sys
from contextlib import asynccontextmanager
from datetime import datetime

from imessage_bot_framework import Bot
from config.production import ProductionConfig
from logging_config import setup_production_logging
from sentry_config import setup_sentry
from health import HealthMonitor

# Setup logging and monitoring
if not ProductionConfig.DEBUG:
    setup_production_logging()
    setup_sentry()

logger = logging.getLogger(__name__)
health_monitor = HealthMonitor()

# Bot configuration
bot = Bot(
    name=ProductionConfig.BOT_NAME or "Production Bot",
    port=ProductionConfig.PORT or 8000,
    debug=ProductionConfig.DEBUG
)

# Graceful shutdown handler
shutdown_event = asyncio.Event()

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_event.set()

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

@bot.app.on_event("startup")
async def startup_event():
    """Application startup tasks."""
    logger.info("Bot starting up...")
    logger.info(f"Configuration: {ProductionConfig.__dict__}")
    
    # Perform startup health checks
    bluebubbles_healthy = await health_monitor.check_bluebubbles(bot)
    if not bluebubbles_healthy:
        logger.error("BlueBubbles server is not healthy!")
    
    logger.info("Bot startup complete")

@bot.app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks."""
    logger.info("Bot shutting down...")
    # Cleanup tasks here
    logger.info("Bot shutdown complete")

# Message handling with monitoring
@bot.on_message
def handle_messages(message):
    """Main message handler with error handling and monitoring."""
    try:
        health_monitor.record_message()
        
        # Your bot logic here
        if message.text.lower() == "ping":
            return "pong!"
        
        return f"Hello! You said: {message.text}"
        
    except Exception as e:
        health_monitor.record_error()
        logger.error(f"Error handling message: {e}", exc_info=True)
        return "Sorry, something went wrong."

# Health check endpoint
@bot.app.get("/health")
async def health_check():
    """Health check for load balancers."""
    await health_monitor.check_bluebubbles(bot)
    report = health_monitor.get_health_report()
    
    # Return 503 if unhealthy
    if report["bluebubbles_status"] != "healthy":
        return JSONResponse(
            status_code=503,
            content=report
        )
    
    return report

@bot.app.get("/metrics")
async def metrics():
    """Metrics endpoint for monitoring."""
    return {
        "messages_processed": health_monitor.message_count,
        "errors": health_monitor.error_count,
        "uptime": time.time() - health_monitor.start_time
    }

async def main():
    """Main application entry point."""
    try:
        logger.info("Starting production bot...")
        
        # Run the bot
        config = uvicorn.Config(
            app=bot.app,
            host="0.0.0.0",
            port=bot.port,
            workers=ProductionConfig.WORKERS,
            access_log=ProductionConfig.DEBUG,
            log_level=ProductionConfig.LOG_LEVEL.lower()
        )
        server = uvicorn.Server(config)
        
        # Run server until shutdown signal
        await server.serve()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
```

## Backup and Recovery

### Data Backup Strategy

```python
# backup.py
import os
import shutil
import sqlite3
import json
from datetime import datetime
from pathlib import Path

class BotBackup:
    """Handle bot data backup and recovery."""
    
    def __init__(self, backup_dir: str = "/opt/backups/bot"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def backup_database(self, db_path: str) -> str:
        """Backup SQLite database."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"database_{timestamp}.db"
        
        # Use SQLite backup API for safe backup
        source = sqlite3.connect(db_path)
        backup = sqlite3.connect(str(backup_file))
        source.backup(backup)
        backup.close()
        source.close()
        
        return str(backup_file)
    
    def backup_config(self, config_data: dict) -> str:
        """Backup configuration data."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"config_{timestamp}.json"
        
        with open(backup_file, 'w') as f:
            json.dump(config_data, f, indent=2, default=str)
        
        return str(backup_file)
    
    def cleanup_old_backups(self, keep_days: int = 30):
        """Remove backups older than specified days."""
        cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
        
        for backup_file in self.backup_dir.glob("*"):
            if backup_file.stat().st_mtime < cutoff_time:
                backup_file.unlink()

# Automated backup
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

backup_manager = BotBackup()
scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('cron', hour=2, minute=0)  # Daily at 2 AM
async def daily_backup():
    """Perform daily backup."""
    try:
        # Backup database if exists
        if os.path.exists("bot_data.db"):
            backup_manager.backup_database("bot_data.db")
        
        # Backup configuration
        config_data = {
            "bot_name": bot.name,
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0"
        }
        backup_manager.backup_config(config_data)
        
        # Cleanup old backups
        backup_manager.cleanup_old_backups(keep_days=30)
        
        logger.info("Daily backup completed successfully")
        
    except Exception as e:
        logger.error(f"Backup failed: {e}", exc_info=True)

# Start scheduler
scheduler.start()
```

## Deployment Scripts

### Deployment Automation

```bash
#!/bin/bash
# deploy.sh - Production deployment script

set -e  # Exit on any error

# Configuration
APP_NAME="imessage-bot"
APP_USER="bot"
APP_DIR="/opt/${APP_NAME}"
BACKUP_DIR="/opt/backups/${APP_NAME}"
VENV_DIR="${APP_DIR}/venv"
REPO_URL="https://github.com/your-org/your-bot.git"
BRANCH="${1:-main}"

echo "🚀 Deploying ${APP_NAME} from branch: ${BRANCH}"

# Create backup
echo "📦 Creating backup..."
sudo -u $APP_USER mkdir -p $BACKUP_DIR
if [ -f "${APP_DIR}/bot_data.db" ]; then
    sudo -u $APP_USER cp "${APP_DIR}/bot_data.db" "${BACKUP_DIR}/bot_data_$(date +%Y%m%d_%H%M%S).db"
fi

# Stop service
echo "🛑 Stopping service..."
sudo systemctl stop $APP_NAME

# Update code
echo "📥 Updating code..."
cd $APP_DIR
sudo -u $APP_USER git fetch origin
sudo -u $APP_USER git reset --hard origin/$BRANCH

# Update dependencies
echo "📋 Installing dependencies..."
sudo -u $APP_USER $VENV_DIR/bin/pip install -r requirements.txt

# Run database migrations (if any)
echo "🗄️ Running migrations..."
if [ -f "migrate.py" ]; then
    sudo -u $APP_USER $VENV_DIR/bin/python migrate.py
fi

# Start service
echo "▶️ Starting service..."
sudo systemctl start $APP_NAME

# Wait for service to be ready
echo "🏥 Checking health..."
for i in {1..30}; do
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then
        echo "✅ Service is healthy!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Service failed to start properly"
        exit 1
    fi
    sleep 2
done

echo "🎉 Deployment completed successfully!"

# Show status
sudo systemctl status $APP_NAME --no-pager
```

Make it executable and use:
```bash
chmod +x deploy.sh
./deploy.sh main  # Deploy main branch
```

## Monitoring and Alerting

### Simple Monitoring Script

```bash
#!/bin/bash
# monitor.sh - Simple monitoring script

APP_NAME="imessage-bot"
HEALTH_URL="http://localhost:8000/health"
ALERT_EMAIL="admin@yourcompany.com"

check_service() {
    # Check systemd service
    if ! systemctl is-active --quiet $APP_NAME; then
        echo "❌ Service $APP_NAME is not running"
        return 1
    fi
    
    # Check health endpoint
    if ! curl -f $HEALTH_URL >/dev/null 2>&1; then
        echo "❌ Health check failed"
        return 1
    fi
    
    echo "✅ Service is healthy"
    return 0
}

# Run check
if ! check_service; then
    # Send alert
    echo "Bot service is down" | mail -s "Alert: Bot Service Down" $ALERT_EMAIL
    
    # Try to restart
    echo "🔄 Attempting to restart service..."
    systemctl restart $APP_NAME
fi
```

Add to cron for regular monitoring:
```bash
# Check every 5 minutes
*/5 * * * * /opt/scripts/monitor.sh >> /var/log/bot-monitor.log 2>&1
```

## See Also

- [Configuration](../core-concepts/configuration.md) - Configuration management
- [Error Handling](../advanced/error-handling.md) - Robust error handling
- [Performance](performance.md) - Performance optimization
- [Testing](testing.md) - Testing strategies 