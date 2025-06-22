# Feedback Bot - Multi-Chat Intelligence

An intelligent feedback collection assistant for early-stage founders that can handle multiple iMessage conversations simultaneously while generating cross-chat insights without compromising user privacy.

## Key Features

### 🎯 Multi-Chat Support
- Monitor multiple chat conversations simultaneously
- Each chat maintains its own conversation context and state
- Concurrent processing of messages across all monitored chats
- Individual conversation histories preserved per chat

### 🧠 Cross-Chat Insights (Privacy-Safe)
- Detect common patterns and themes across conversations without revealing private information
- Generate privacy-safe probes based on insights from other conversations
- Automatically ask related questions in different chats when patterns emerge
- No personal information is shared between chats

### 📊 Mom Test Methodology
- Implements Rob Fitzpatrick's "Mom Test" principles for customer interviews
- Asks probing questions that uncover real problems and needs
- Avoids leading questions and idea validation
- Focuses on past behavior and actual problems

### 🔄 Intelligent Conversation Flow
- Adaptive conversation states (Initial Contact → Collecting Feedback → Probing Deeper → Summarizing)
- Natural multi-message responses that simulate real texting
- Context-aware responses based on conversation history
- Automatic summarization after reaching question limits

## Configuration

### Environment Variables

```bash
# Multiple Chat GUIDs (comma-separated)
CHAT_GUIDS=chat-guid-1,chat-guid-2,chat-guid-3

# Cross-Chat Insights Settings
ENABLE_CROSS_CHAT_INSIGHTS=true        # Enable cross-chat pattern detection
CROSS_CHAT_PROBE_FREQUENCY=0.3         # 30% chance to ask cross-chat probes

# Bot Configuration
FOUNDER_NAME=YourName                   # How the bot identifies itself
PRODUCT_NAME=YourProduct               # Product being tested
MAX_QUESTIONS_PER_SESSION=3            # Max questions per conversation

# BlueBubbles Integration
BLUEBUBBLES_SERVER_URL=http://localhost:1234
BLUEBUBBLES_PASSWORD=your-password

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key
```

## How Cross-Chat Insights Work

### Privacy Protection
1. **No Personal Information Shared**: Individual messages are never shared between chats
2. **Anonymized Patterns**: Only general themes are tracked (e.g., "payment_issues", "performance_issues")
3. **Hashed Chat IDs**: Chat GUIDs are hashed to prevent identification
4. **Aggregated Insights**: Only patterns that appear across multiple chats trigger probes

### Insight Generation Process
1. **Theme Detection**: Messages are analyzed to identify general themes
2. **Pattern Recognition**: When the same theme appears in multiple chats, it becomes an "insight"
3. **Cross-Chat Probes**: Generic questions about the theme are generated for other chats
4. **Concurrent Delivery**: Probes are sent to relevant chats simultaneously

### Example Flow
```
Chat A: "The payment system keeps failing"
→ Theme: "payment_issues" detected

Chat B: Gets probe: "How do you handle payment-related problems?"
Chat C: Gets probe: "What's your typical flow when making payments?"
```

## API Endpoints

### Core Endpoints
- `POST /webhook` - Handle BlueBubbles webhooks
- `GET /stats` - Get comprehensive statistics across all chats
- `GET /cross-chat-insights` - View detected patterns and themes
- `GET /conversation/{chat_guid}` - Get specific conversation details

### Statistics Response
```json
{
  "feedback_collection": {
    "total_conversations": 15,
    "active_conversations": 8,
    "total_feedback_items": 47,
    "monitored_chats": 3,
    "cross_chat_insights": {
      "payment_issues": {
        "frequency": 5,
        "affected_chats": 3,
        "severity": "high",
        "theme": "payment_issues"
      }
    }
  }
}
```

## Installation & Setup

1. **Install Dependencies**
```bash
cd src/bots/feedback-bot
poetry install
```

2. **Configure Environment**
```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

3. **Get Chat GUIDs from BlueBubbles**
   - Open BlueBubbles web interface
   - Navigate to the chats you want to monitor
   - Copy the chat GUIDs from the URL or API

4. **Run the Bot**
```bash
poetry run python main.py
```

## Conversation Flow

### State Machine
```
Initial Contact → Collecting Feedback → Probing Deeper → Summarizing → Thanking
                                   ↓
                           Cross-Chat Insights
                                   ↓
                        Concurrent Probes to Other Chats
```

### Response Types
1. **Welcome Messages**: Warm introduction when users first interact
2. **Acknowledgment**: Brief responses that show active listening
3. **Mom Test Probes**: Questions that uncover real problems and needs
4. **Cross-Chat Probes**: Generic questions based on patterns from other conversations
5. **Summaries**: Thoughtful recapping of feedback collected

## Privacy & Security

### Data Handling
- **No Message Storage**: Individual messages are not permanently stored
- **Anonymized Insights**: Only general themes are tracked, not specific content
- **Chat Isolation**: Each conversation remains completely separate
- **Hashed Identifiers**: Chat GUIDs are hashed for insight tracking

### Cross-Chat Probe Guidelines
- Only generic, theme-based questions are generated
- No personal information from other chats is revealed
- Probes are based on patterns, not specific incidents
- Users cannot tell that insights came from other conversations

## Monitoring & Analytics

### Available Metrics
- Total conversations across all chats
- Active conversations (last 24 hours)
- Feedback breakdown by type
- Cross-chat insight effectiveness
- Response generation performance

### Health Check
Access `GET /` for a comprehensive health check including:
- Configuration status
- Number of monitored chats
- Cross-chat insights status
- Recent activity summary

## Development

### Architecture
- **FastAPI**: Async web framework for webhook handling
- **Pydantic**: Data validation and modeling
- **OpenAI GPT-4o**: AI-powered response generation
- **BlueBubbles API**: iMessage integration

### Key Components
- `main.py`: Webhook handling and concurrent message processing
- `conversation_state.py`: Multi-chat state management and cross-chat insights
- `feedback_ai.py`: AI response generation with privacy protection
- `models.py`: Data models including cross-chat insight tracking
- `config.py`: Multi-chat configuration management

### Testing Cross-Chat Features
1. Set up multiple test chats in BlueBubbles
2. Send similar feedback themes to different chats
3. Monitor `/cross-chat-insights` endpoint
4. Verify probes are generated for other chats
5. Confirm no private information leaks between chats

## Troubleshooting

### Common Issues
- **Multiple Chat GUIDs Not Working**: Ensure `CHAT_GUIDS` is comma-separated without spaces
- **Cross-Chat Probes Not Generating**: Check `ENABLE_CROSS_CHAT_INSIGHTS=true` and frequency settings
- **AI Responses Too Generic**: Adjust `CROSS_CHAT_PROBE_FREQUENCY` to balance personalization

### Logs
Enable debug logging with `DEBUG=true` to see:
- Multi-chat message routing
- Cross-chat insight generation
- Concurrent probe delivery
- Privacy protection measures

This bot transforms customer feedback collection from a one-on-one process into an intelligent, multi-conversation system that learns from patterns while respecting individual privacy. 

# Linear Integration

The bot includes powerful Linear integration that automatically converts collected feedback into actionable issues:

### Features

- **Intelligent Triaging**: GPT-4o analyzes all feedback and groups related items together
- **Priority Assignment**: Automatically assigns priority based on feedback type and severity
- **Rich Markdown Descriptions**: Creates detailed issue descriptions with user quotes and context
- **Cross-Chat Insights**: Includes patterns detected across multiple conversations
- **Privacy-Safe**: Anonymizes user information while preserving actionable insights
- **⭐ Automatic Session Triaging**: Creates Linear issues when feedback sessions end
- **📊 Comprehensive Logging**: Detailed logs for every step of the triaging process

### Usage

#### Automatic Triaging (Recommended)

The bot automatically creates Linear issues when feedback sessions end:

```bash
# Sessions automatically end when:
# - Bot reaches summarizing state
# - Maximum questions asked (default: 3)
# - User provides sufficient feedback detail

# Comprehensive logging shows:
# 🎯 Feedback session ending for chat xyz - triggering automatic Linear triaging
# 📊 Chat session xyz feedback summary: Total feedback items: 2
# 🤖 Formatting feedback with GPT-4o for chat session xyz
# ✅ GPT-4o formatted 1 issues for chat session xyz
# 🚀 Creating Linear issue 1/1 for chat session xyz
# ✅ Created Linear issue for chat session xyz: PROD-123: App crashes on notifications
# 🎉 Auto-triaging completed for chat session xyz
```

#### Manual Triaging

You can also manually trigger triaging for all conversations:

1. **Triage All Feedback**:
   ```bash
   curl -X POST http://localhost:8081/triage-to-linear
   ```

2. **Check Linear Status**:
   ```bash
   curl http://localhost:8081/linear-status
   ```

3. **Manual Testing**:
   ```bash
   poetry run python test_linear.py
   ```

### API Endpoints

- `GET /linear-status` - Check Linear integration status and configuration
- `POST /triage-to-linear` - Triage all collected feedback into Linear issues
- `GET /feedback-summary` - Get summary of collected feedback ready for triaging

### Workflow

#### Automatic Session-End Triaging

1. **Session Detection**: Bot detects when feedback sessions are ending
2. **Feedback Collection**: Gathers all feedback from that specific chat session
3. **Cross-Chat Context**: Includes relevant insights from other conversations
4. **GPT-4o Processing**: AI formats feedback into structured Linear issues
5. **Issue Creation**: Creates issues in Linear with session context
6. **Comprehensive Logging**: Detailed logs track every step
7. **Session Marking**: Marks session as triaged to prevent duplicates

#### Manual All-Chat Triaging

1. **Collect Feedback**: Bot collects feedback from multiple chat conversations
2. **Process with GPT-4o**: AI analyzes and structures all feedback items
3. **Group & Prioritize**: Related feedback is grouped into single issues with appropriate priority
4. **Create Issues**: Structured issues are created in Linear with rich descriptions
5. **Track Results**: Bot reports which issues were created successfully

### Issue Format

Generated Linear issues include:

- **Clear Titles**: Concise, actionable summaries
- **Detailed Descriptions**: 
  - Problem statement
  - User impact assessment
  - Anonymized user quotes
  - Cross-chat insights (if applicable)
  - Suggested next steps
  - **Session Context**: Information about the specific feedback session
- **Appropriate Priority**: Based on feedback type and severity
- **Rich Markdown**: Properly formatted with headers, lists, and emphasis

### Session Context

Each automatically created issue includes session context:

```markdown
---
**Session Context:**
- Chat Session: abc12345... (anonymized)
- Session State: summarizing
- Total Questions Asked: 3
- Feedback Items: 2
- Created: 2024-01-15 14:30 UTC
```

### Logging Examples

The bot provides comprehensive logging for triaging operations:

```bash
# Session ending detection
🎯 Feedback session ending for chat abc123... - triggering automatic Linear triaging
   Previous state: probing_deeper
   Current state: summarizing
   Total feedback collected: 2
   Questions asked: 3

# Feedback collection
📊 Chat session abc123... feedback summary:
   Total feedback items: 2
   Session state: summarizing
   Questions asked: 3

# Cross-chat insights
🔗 Found 1 relevant cross-chat insights for session abc123...

# GPT-4o processing
🤖 Formatting feedback with GPT-4o for chat session abc123...
✅ GPT-4o formatted 1 issues for chat session abc123...

# Linear issue creation
🚀 Creating Linear issue 1/1 for chat session abc123...
   Title: App crashes when opening notifications
   Type: bug_report
   Priority: high

# Success confirmation
✅ Created Linear issue for chat session abc123...:
   Issue ID: PROD-123
   Title: App crashes when opening notifications
   URL: https://linear.app/company/issue/PROD-123
   Priority: high

# Session completion
🎉 Auto-triaging completed for chat session abc123...
   Created 1 Linear issues:
   ✅ PROD-123: App crashes when opening notifications
```

## API Endpoints

### Core Endpoints

- `GET /` - Health check and bot status
- `POST /webhook` - BlueBubbles webhook endpoint for receiving messages
- `GET /stats` - Comprehensive bot statistics

### Feedback Endpoints

- `GET /feedback-summary` - Summary of all collected feedback
- `GET /cross-chat-insights` - Privacy-safe insights across conversations
- `GET /conversation/{chat_guid}` - Information about a specific conversation

### Linear Integration Endpoints

- `GET /linear-status` - Linear integration status
- `POST /triage-to-linear` - Triage feedback to Linear issues

## Mom Test Methodology

The bot implements Mom Test principles for better customer discovery:

- **Avoids Leading Questions**: Doesn't validate ideas with flattery
- **Focuses on Past Behavior**: Asks about specific situations and actions
- **Uncovers Root Problems**: Digs beneath feature requests to understand underlying needs
- **Seeks Specific Details**: Gets concrete information rather than general opinions

### Example Question Flow

1. **User**: "Your app is slow"
2. **Bot**: "Ah gotcha - when's the last time this happened to you?"
3. **User**: "This morning when I was trying to upload photos"
4. **Bot**: "What were you trying to do right before it got slow?"
5. **User**: "I was uploading like 20 photos from my vacation"
6. **Bot**: "How often do you need to upload that many photos at once?"

*🔄 Session ends → Auto-creates Linear issue: "Photo upload performance degrades with large batches"*

## Privacy & Security

### Data Handling
- **No Message Storage**: Individual messages are not permanently stored
- **Anonymized Insights**: Only general themes are tracked, not specific content
- **Chat Isolation**: Each conversation remains completely separate
- **Hashed Identifiers**: Chat GUIDs are hashed for insight tracking

### Cross-Chat Probe Guidelines
- Only generic, theme-based questions are generated
- No personal information from other chats is revealed
- Probes are based on patterns, not specific incidents
- Users cannot tell that insights came from other conversations

### Session Tracking
- **Session Tracking**: Each session is tracked independently for targeted issue creation
- **Optional Data Clearing**: Feedback can be cleared after triaging (configurable)

## Development

### Running Tests

```bash
# Test Linear integration
poetry run python test_linear.py

# Run all tests
poetry run pytest
```

### Code Quality

```bash
# Format code
poetry run black .

# Type checking
poetry run mypy .

# Linting
poetry run flake8
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   iMessage      │    │   Feedback Bot   │    │    Linear       │
│   (BlueBubbles) │───▶│                  │───▶│    Issues       │
└─────────────────┘    │  ┌─────────────┐ │    └─────────────────┘
                       │  │ Conversation│ │
                       │  │   Manager   │ │    ┌─────────────────┐
                       │  │   GPT-4o    │ │───▶│   Processing    │
                       │  └─────────────┘ │    └─────────────────┘
                       │  ┌─────────────┐ │
                       │  │ Auto-Triage │ │
                       │  │   System    │ │
                       │  └─────────────┘ │
                       │  ┌─────────────┐ │
                       │  │ Linear      │ │
                       │  │ Integration │ │
                       │  └─────────────┘ │
                       └──────────────────┘
```

## Troubleshooting

### Linear Integration Issues

1. **Check API Key**: Ensure your Linear API key is valid and has the right permissions
2. **Test Connection**: Run `python test_linear.py` to verify connectivity
3. **Check Team Configuration**: Verify your team key is correct or let it auto-select
4. **Review Logs**: Check bot logs for detailed error messages
5. **Session Tracking**: Look for auto-triaging logs to see if sessions are being detected

### Common Issues

- **"No teams found"**: Check your Linear API key and permissions
- **"Team not found"**: Verify your `LINEAR_TEAM_KEY` setting
- **"GPT-4o formatting failed"**: Check your OpenAI API key and quota
- **"Session not auto-triaging"**: Check `AUTO_TRIAGE_ON_SESSION_END` setting
- **"No feedback items found"**: Ensure users are providing actual feedback (not just questions)

### Auto-Triaging Debug

If automatic triaging isn't working:

1. **Check Configuration**:
   ```bash
   # Ensure these are set to true
   ENABLE_LINEAR_INTEGRATION=true
   AUTO_TRIAGE_ON_SESSION_END=true
   ```

2. **Monitor Logs**: Look for these log patterns:
   ```bash
   # Session ending detection
   🎯 Feedback session ending for chat...
   
   # Feedback collection
   📊 Chat session ... feedback summary
   
   # Issue creation
   ✅ Created Linear issue for chat session...
   ```

3. **Test Manually**: Use the manual endpoints to verify Linear connectivity

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details. 