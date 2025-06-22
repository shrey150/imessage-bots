# Stagehand LinkedIn Scraper Setup Guide

## Overview

The Resume Roast Bot now uses Stagehand for LinkedIn profile scraping, providing more reliable and comprehensive data extraction using AI-powered browser automation. Stagehand is absolutely goated for this type of task!

## Prerequisites

### System Requirements

1. **Node.js** (v18 or higher)
   ```bash
   # Install Node.js from https://nodejs.org/
   # Or using Homebrew on macOS:
   brew install node
   
   # Verify installation
   node --version
   npm --version
   ```

2. **Python** (v3.9 or higher) - already required for the bot

### API Keys

You'll need the following API keys in your `.env` file:

```env
# Required
OPENAI_API_KEY=your_openai_api_key_here

# LinkedIn Authentication (Required for profile access)
LINKEDIN_EMAIL=your.linkedin.email@example.com
LINKEDIN_PASSWORD=your_linkedin_password

# Optional (for enhanced performance and avoiding local browser limitations)
BROWSERBASE_API_KEY=your_browserbase_api_key_here
BROWSERBASE_PROJECT_ID=your_browserbase_project_id_here

# Existing BlueBubbles configuration
BLUEBUBBLES_SERVER_URL=http://localhost:1234
BLUEBUBBLES_PASSWORD=your-server-password
CHAT_GUID=your-chat-guid
```

## Installation

### 1. Update Python Dependencies

The existing `pyproject.toml` should handle the Python dependencies. Run:

```bash
cd src/bots/resume-roast
poetry install
```

### 2. Set Up Node.js Environment

Ensure Node.js is available in your system PATH. The Stagehand scraper will automatically install its dependencies in temporary directories when needed.

### 3. Configure Environment Variables

Create or update your `.env` file with the required API keys (see above).

## How It Works

### Stagehand Integration

The new `stagehand_scraper.py` module:

1. **Authenticates with LinkedIn** using your credentials for reliable profile access
2. **Dynamically creates Node.js scripts** that use Stagehand to scrape LinkedIn profiles
3. **Installs dependencies** automatically in temporary directories
4. **Extracts comprehensive data** using Stagehand's AI-powered extraction capabilities
5. **Returns structured data** that's compatible with the existing bot architecture

### Enhanced Data Extraction

Compared to the old scraper, Stagehand provides:

- **Name and headline** (same as before)
- **Current position** with more details
- **Location** information
- **About/summary** section content
- **Work experience** with descriptions and durations
- **Education** with degrees, fields, and durations
- **Skills** list
- **Connection count**
- **Raw text context** for better roasting material

### GPT-4o Integration

The enhanced profile data is passed to GPT-4o with improved context:

- More detailed work experience descriptions
- Skills and education information
- Location and connection data
- Raw text context for additional insights

## Usage

### Basic Usage (Same as Before)

The bot usage remains the same for end users:

1. Start a conversation with the bot
2. Send a LinkedIn profile URL
3. Wait for the roast to be generated

### Enhanced Roasting

The roasts are now more targeted and insightful thanks to:

- **Deeper profile analysis** from Stagehand
- **Better context understanding** from comprehensive data extraction
- **More specific observations** about career patterns and choices

## Configuration Options

### Local vs Remote Browser

**Local Mode (Default):**
- Uses your local Chrome/Chromium browser
- No additional API keys required beyond OpenAI
- May have some limitations with LinkedIn's anti-bot measures

**Browserbase Mode (Recommended):**
- Uses Browserbase's cloud browser infrastructure
- More reliable for consistent scraping
- Better handling of anti-bot measures
- Requires Browserbase API credentials

To enable Browserbase mode, add your API credentials to the `.env` file.

### Performance Tuning

The scraper includes several optimizations:

- **Caching**: Stagehand's built-in action caching
- **Structured extraction**: Using Zod schemas for reliable data parsing
- **Error handling**: Comprehensive fallback mechanisms
- **Timeout management**: Reasonable timeouts for reliable operation

## Troubleshooting

### Common Issues

1. **Node.js not found**
   ```
   Error: npm/node command not found
   ```
   **Solution**: Install Node.js and ensure it's in your PATH

2. **Permission denied**
   ```
   Error: Permission denied when creating temporary directory
   ```
   **Solution**: Check directory permissions or run with appropriate privileges

3. **LinkedIn blocking**
   ```
   Error: Failed to scrape profile - access blocked
   ```
   **Solutions**: 
   - Ensure your LinkedIn credentials are correct
   - Try using Browserbase mode for better IP reputation
   - Wait and retry later
   - Check if your LinkedIn account requires 2FA verification

4. **OpenAI API errors**
   ```
   Error: OpenAI API rate limit exceeded
   ```
   **Solution**: Check your OpenAI API usage and limits

### Debug Mode

To enable verbose logging, set `DEBUG=true` in your `.env` file.

## Benefits Over Previous Scraper

1. **More Reliable**: AI-powered element selection vs brittle CSS selectors
2. **Richer Data**: Comprehensive profile information extraction
3. **Better Handling**: Improved anti-bot detection avoidance
4. **Future-Proof**: Adaptable to LinkedIn UI changes
5. **Enhanced Roasts**: More context leads to better, more specific roasts

## Security Considerations

- Node.js scripts are created dynamically but use safe, parameterized templates
- Temporary directories are cleaned up automatically
- No user input is directly executed as code
- API keys and credentials are handled securely through environment variables
- LinkedIn credentials are passed securely to the scraping process

## LinkedIn Authentication & 2FA

The scraper automatically handles LinkedIn login using your credentials. If your LinkedIn account has Two-Factor Authentication (2FA) enabled:

1. The scraper will detect verification challenges
2. It will wait up to 30 seconds for manual intervention
3. You may need to complete the 2FA process manually in the browser
4. The scraper will then continue with profile extraction

**Recommendation:** For automation purposes, consider using a LinkedIn account without 2FA, or ensure you're available to handle 2FA prompts when the bot is running.

## Development

### Testing the Scraper

You can test the scraper independently:

```python
import asyncio
from stagehand_scraper import stagehand_linkedin_scraper

async def test_scraper():
    url = "https://linkedin.com/in/your-test-profile"
    profile = await stagehand_linkedin_scraper.scrape_profile(url)
    print(profile)

asyncio.run(test_scraper())
```

### Customizing Extraction

The extraction schema in `stagehand_scraper.py` can be modified to capture additional fields or change the extraction logic.

## Support

For issues with:
- **Stagehand**: Check the [official documentation](https://docs.stagehand.dev/)
- **Browserbase**: Visit [Browserbase docs](https://docs.browserbase.com/)
- **This integration**: Check the bot logs and ensure all dependencies are properly installed 