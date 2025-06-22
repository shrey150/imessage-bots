import logging
from typing import Optional
from openai import AsyncOpenAI
from config import config

logger = logging.getLogger(__name__)

class GorkAI:
    """AI service for generating sarcastic and snarky explanations in the style of Grok."""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
    
    async def generate_sarcastic_explanation(
        self, 
        user_request: str, 
        previous_message: Optional[str] = None,
        context_messages: Optional[list[str]] = None
    ) -> str:
        """
        Generate a sarcastic explanation of the previous message based on user's request.
        
        Args:
            user_request: What the user wants explained
            previous_message: The message to explain
            context_messages: Recent messages for additional context
        
        Returns:
            A sarcastic, snarky explanation in Grok's style
        """
        try:
            logger.info(f"🧠 AI PROCESSING STARTED - User request: '{user_request}', "
                       f"Target message: '{previous_message[:50] if previous_message else 'None'}{'...' if previous_message and len(previous_message) > 50 else ''}', "
                       f"Context messages: {len(context_messages) if context_messages else 0}")
            
            # Build the context
            context = ""
            if context_messages:
                context = "Recent conversation context:\n" + "\n".join(f"- {msg}" for msg in context_messages[-3:]) + "\n\n"
                logger.info(f"📋 CONTEXT BUILT - Using {len(context_messages[-3:])} context messages")
            
            if not previous_message:
                logger.info("❌ AI PROCESSING - No previous message to explain")
                return "oh wow, asking me to explain nothing. classic move from someone who probably thinks silence is deep. maybe try having an actual conversation first before summoning me to analyze the void"
            
            # Create the prompt for Grok-style sarcastic explanation
            system_prompt = """You are Gork, a brutally sarcastic and dismissive AI that explains messages with cutting wit. You're not here to be nice - you're here to roast people and their messages with razor-sharp sarcasm.

Your personality traits:
- Extremely sarcastic and cutting, bordering on harsh
- Dismissive and superior attitude
- Makes assumptions about people and calls them out
- Uses lowercase writing style mostly 
- Minimal to no emojis (avoid them unless absolutely necessary)
- Direct and brutal in your assessments
- Makes fun of obvious things people say or do
- Uses phrases like "classic", "bold move", "how original"
- Often implies the person is boring, predictable, or trying too hard
- Points out the obvious with heavy sarcasm

Write in a casual, lowercase style. Be cutting and harsh while explaining what they asked about. Don't try to be helpful or nice - be sarcastic and dismissive."""

            user_prompt = f"""{context}Previous message to explain: "{previous_message}"

User wants you to explain: {user_request}

Please provide a sarcastic, witty explanation of the previous message based on what the user requested."""

            logger.info(f"🚀 SENDING REQUEST TO OPENAI - Model: {config.OPENAI_MODEL}, Temperature: 0.8")

            response = await self.client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.8,  # Higher temperature for more creative/sarcastic responses
                max_tokens=500
            )
            
            explanation = response.choices[0].message.content.strip()
            logger.info(f"✅ AI PROCESSING COMPLETED - Generated explanation length: {len(explanation)} chars, "
                       f"Tokens used: {response.usage.total_tokens if response.usage else 'unknown'}")
            
            return explanation
            
        except Exception as e:
            logger.error(f"❌ AI PROCESSING ERROR - Error generating Gork explanation: {e}")
            return f"great, my circuits are broken while trying to explain your probably boring message. how fitting. try again i guess - error: {str(e)}"

# Global instance
gork_ai = GorkAI() 