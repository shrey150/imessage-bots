# iMessage Bot Framework Documentation

Welcome to the comprehensive documentation for the **iMessage Bot Framework** - a Python SDK that makes building iMessage bots simple and powerful.

## 🌟 What is iMessage Bot Framework?

The iMessage Bot Framework is a modern Python SDK that simplifies creating intelligent iMessage bots by abstracting away the complexity of BlueBubbles webhook handling while providing full access to advanced features when needed.

## 📚 Documentation Structure

### Getting Started
- [Installation](getting-started/installation.md) - Install and set up the framework
- [Quick Start](getting-started/quick-start.md) - Build your first bot in minutes
- [Project Structure](getting-started/project-structure.md) - Understanding the framework layout

### Core Concepts
- [Bot Architecture](core-concepts/bot-architecture.md) - How the framework works
- [Message Handling](core-concepts/message-handling.md) - Processing incoming messages
- [State Management](core-concepts/state-management.md) - Persistent data storage
- [Configuration](core-concepts/configuration.md) - Environment setup and config

### API Reference
- [Bot Class](api-reference/bot-class.md) - Main Bot class documentation
- [Message Class](api-reference/message-class.md) - Message objects and methods
- [Chat Class](api-reference/chat-class.md) - Chat interaction methods
- [Decorators](api-reference/decorators.md) - Built-in decorators and patterns

### Advanced Features
- [Custom API Endpoints](advanced/custom-endpoints.md) - Adding FastAPI routes
- [Middleware](advanced/middleware.md) - Request/response processing
- [BlueBubbles Integration](advanced/bluebubbles-api.md) - Direct API access
- [Error Handling](advanced/error-handling.md) - Robust error management

### Examples & Tutorials
- [Basic Echo Bot](examples/echo-bot.md) - Simple message echoing
- [Command Bot](examples/command-bot.md) - Handling bot commands
- [AI Chat Bot](examples/ai-bot.md) - Integrating with AI services
- [Advanced Patterns](examples/advanced-patterns.md) - Complex bot behaviors

### Best Practices
- [Code Organization](best-practices/code-organization.md) - Structuring your bot project
- [Testing](best-practices/testing.md) - Testing bot functionality
- [Deployment](best-practices/deployment.md) - Production deployment guide
- [Performance](best-practices/performance.md) - Optimization tips

### CLI Tools
- [CLI Overview](cli/overview.md) - Command-line interface
- [Project Creation](cli/project-creation.md) - Creating new bot projects
- [Development Tools](cli/development-tools.md) - Development utilities

## 🚀 Key Features

- **Simple Message Handling**: Decorator-based message processing
- **FastAPI Integration**: Built-in web server with custom endpoint support
- **BlueBubbles Compatible**: Full integration with BlueBubbles server
- **Type Safety**: Complete TypeScript-style typing for Python
- **Extensible**: Easy to add custom functionality
- **Production Ready**: Logging, error handling, and monitoring built-in

## 💡 Quick Example

```python
from imessage_bot_framework import Bot

bot = Bot("My First Bot")

@bot.on_message
def handle_message(message):
    if message.text.lower() == "hello":
        return f"Hi there! You said: {message.text}"

@bot.app.get("/status")
async def bot_status():
    return {"status": "running", "bot": "awesome"}

if __name__ == "__main__":
    bot.run()
```

## 🛠️ Requirements

- Python 3.8+
- BlueBubbles Server
- macOS (for BlueBubbles server)

## 📖 Need Help?

- Check out our [examples](examples/) for practical implementations
- Read the [API Reference](api-reference/) for detailed documentation
- Follow [best practices](best-practices/) for production-ready bots

## 🤝 Contributing

Want to contribute? Check out our [Contributing Guide](../CONTRIBUTING.md) for development setup and guidelines.

---

**Ready to get started?** Jump to the [Installation Guide](getting-started/installation.md) to begin building your first iMessage bot! 