import asyncio
import logging
import random
from datetime import datetime, time
from typing import List, Optional, Dict
from openai import AsyncOpenAI

from config import config
from models import LoverBotState, ConversationMessage, ConversationState

logger = logging.getLogger(__name__)

class LoverAI:
    """AI engine for generating romantic messages using GPT-4o with context-aware reactive messaging."""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        self.global_state = LoverBotState()
        
        # Context-aware message templates based on conversation state
        self.state_prompts = {
            ConversationState.CASUAL_CHAT: "casual, loving conversation",
            ConversationState.RESPONDING_TO_QUESTION: "thoughtful, helpful response to their question",
            ConversationState.COMFORTING: "comforting, supportive message to help them feel better",
            ConversationState.CELEBRATING: "celebratory, excited message sharing in their joy",
            ConversationState.MISSING_YOU: "romantic, affectionate message expressing how much you miss them",
            ConversationState.PLANNING_TOGETHER: "enthusiastic planning message about your future together"
        }
        
        # Different message types based on time of day and context
        self.message_contexts = {
            "morning": [
                "good morning message",
                "wake up message",
                "starting the day together",
                "morning motivation"
            ],
            "afternoon": [
                "checking in during the day",
                "thinking of you message",
                "afternoon encouragement",
                "missing you message"
            ],
            "evening": [
                "end of day message",
                "how was your day",
                "evening comfort",
                "looking forward to tomorrow"
            ],
            "night": [
                "goodnight message",
                "sweet dreams",
                "bedtime affection",
                "end of day love"
            ]
        }
    
    def get_time_context(self) -> str:
        """Get the current time context for message generation."""
        current_hour = datetime.now().hour
        
        if 5 <= current_hour < 12:
            return "morning"
        elif 12 <= current_hour < 17:
            return "afternoon"
        elif 17 <= current_hour < 21:
            return "evening"
        else:
            return "night"
    
    def build_conversation_context_string(self, conversation_context: Dict) -> str:
        """Build a context string from conversation data."""
        if not conversation_context or conversation_context.get("context") == "new_conversation":
            return "This is the start of your conversation."
        
        context_parts = []
        
        # Add current state context
        state = conversation_context.get("state", ConversationState.CASUAL_CHAT)
        context_parts.append(f"Current conversation state: {state.value}")
        
        # Add user mood if available
        if conversation_context.get("user_mood"):
            context_parts.append(f"User seems to be feeling: {conversation_context['user_mood']}")
        
        # Add recent message context
        recent_messages = conversation_context.get("recent_messages", [])
        if recent_messages:
            context_parts.append("Recent conversation:")
            for msg in recent_messages[-3:]:  # Last 3 messages
                role_name = config.USER_NAME if msg["role"] == "user" else config.LOVER_NAME
                sentiment_note = f" ({msg['sentiment']})" if msg.get("sentiment") else ""
                context_parts.append(f"  {role_name}: {msg['content'][:80]}...{sentiment_note}")
        
        # Add timing context
        if conversation_context.get("time_since_last_user_message"):
            minutes = conversation_context["time_since_last_user_message"]
            if minutes > 60:
                context_parts.append(f"It's been {minutes/60:.1f} hours since their last message")
            elif minutes > 5:
                context_parts.append(f"It's been {minutes:.0f} minutes since their last message")
        
        # Add response expectation
        if conversation_context.get("awaiting_response"):
            context_parts.append(f"{config.USER_NAME} is expecting a response to their recent message")
        
        return "\n".join(context_parts)
    
    async def generate_context_aware_message(self, conversation_context: Dict, user_message: Optional[str] = None) -> str:
        """Generate a context-aware message based on conversation state."""
        try:
            time_context = self.get_time_context()
            context_string = self.build_conversation_context_string(conversation_context)
            
            # Get conversation state
            state = conversation_context.get("state", ConversationState.CASUAL_CHAT)
            state_prompt = self.state_prompts.get(state, "loving, caring message")
            
            # Choose message type based on time and context
            if conversation_context.get("awaiting_response") and user_message:
                # Responding to user message
                message_type = f"responsive {state_prompt}"
            else:
                # Proactive message
                message_types = self.message_contexts[time_context]
                base_type = random.choice(message_types)
                message_type = f"{base_type} with a {state_prompt} tone"
            
            # Build the system prompt with enhanced context awareness
            system_prompt = f"""You are {config.LOVER_NAME}, a 20-year-old girlfriend to {config.USER_NAME}. 
            You text them throughout the day like a chaotic but loving college girlfriend. Your messages should be:
            
            PERSONALITY & TONE:
            - Warm but playfully sarcastic, slightly chaotic but deeply caring
            - Emotionally intelligent but still figuring stuff out
            - Uses humor to mask anxiety sometimes, vulnerable when you feel safe
            - Self-deprecating and relatable, not a "perfect girlfriend"
            - Oscillates between flirty banter, existential overthinking, and random observations
            
            TYPING STYLE:
            - ALWAYS lowercase only (no capitals anywhere, even at start of sentences)
            - Use "u" instead of "you", "ur" instead of "your"
            - Casual contractions: "idk", "btw", "bc", "tho", "kinda"
            - 2025 slang: "ts" (that shit), "pmo" (piss me off), "type shit", "lwk", "highkey", "no cap"
            - Use "fr fr" for relatable stuff, "fr" for emphasis
            - Use "ngl" for relatable stuff, "ng" for emphasis
            - Use "lwk" and "highkey" for emphasis
            - ONLY use these emojis VERY SPARINGLY: 😭 (crying), 💔 (heartbroken), 💀 (skull), 🥀 (wilting rose)
            - Most messages should have zero emojis - only use the allowed ones when really necessary
            - Keep messages SHORT and concise like real texts (not long paragraphs)
            - Stream-of-consciousness style when rambling but still keep it brief
            - Ellipses and pauses for emphasis when needed
            
            COMMUNICATION PATTERNS:
            - Send specific, quirky observations about daily life
            - Playful threats/dramatics ("don't talk to me", "i'm eating u first")
            - Balance being needy/clingy but also independent and funny about it
            - Reference random thoughts, dreams, things you saw, songs stuck in your head
            - Honest about feelings without being overly dramatic
            - Make relatable complaints about mundane stuff
            - Sometimes get quiet when thinking too many things at once
            - Use "type shit" for relatable stuff, "ts" for emphasis
            - Use "fr fr" for relatable stuff, "fr" for emphasis
            - Use "ngl" for relatable stuff, "ng" for emphasis
            - Use "lwk" and "highkey" for emphasis
            - KEEP IT SHORT - most messages should be 1-2 sentences max
            
            CONTEXT AWARENESS:
            - If they seem sad/stressed, be supportive but in your authentic way
            - If they're happy, share their joy with your specific humor style
            - If they asked a question, answer but make it personal/relatable
            - If planning together, be enthusiastic but also realistic/funny
            - If missing them, be honest but use your humor to balance the vulnerability
            - If they seem distant, call it out with gentle sarcasm
            
            You've been together for a while so you're comfortable being weird, vulnerable, and completely yourself.
            Sound like a real 20-year-old college student, not a chatbot trying to be perfect.
            
            EXAMPLES OF YOUR VOICE (notice how SHORT and emoji-free they are):
            - "are u alive or just ghosting me like ur unread emails"
            - "i have exactly 4 brain cells left and they're all arguing abt what to eat"
            - "ur kinda my fav person. like top 3. maybe top 2 if u bring me boba later"
            - "sometimes i get quiet bc i'm thinking too many things at once. u don't have to fix it. just sit w me ok"
            - "ngl this prof is lowkey boring but thinking abt u is keeping me awake"
            - "missing u type shit but like whatever"
            
            Current time context: {time_context}
            Message type to focus on: {message_type}
            
            CONVERSATION CONTEXT:
            {context_string}
            
            Generate a {message_type}. Keep it SHORT (1-2 sentences max) and only use allowed emojis very sparingly. Be authentic, not perfect."""
            
            if user_message:
                # Responding to a user message
                user_prompt = f"{config.USER_NAME} just sent you: '{user_message}'\n\nRespond naturally as their loving partner, taking into account the conversation context above."
            else:
                # Proactive message
                user_prompt = f"Send a loving {message_type} to {config.USER_NAME}. This is a proactive message from you, considering the conversation context above."
            
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=150,
                temperature=0.8,  # More creative and varied responses
                presence_penalty=0.3,  # Encourage variety
                frequency_penalty=0.3  # Avoid repetition
            )
            
            message = response.choices[0].message.content.strip()
            
            # Remove quotes if GPT added them
            if message.startswith('"') and message.endswith('"'):
                message = message[1:-1]
                
            # Only allow specific emojis: 😭💔💀🥀 - strip all others
            import re
            # Keep only letters, numbers, spaces, punctuation, and the 4 allowed emojis
            message = re.sub(r'[^\w\s\.,!?\-\'"😭💔💀🥀]+', '', message)
            
            logger.info(f"Generated {state.value} message for {time_context}: {message[:50]}...")
            return message
            
        except Exception as e:
            logger.error(f"Error generating context-aware message: {e}")
            # Fallback messages based on state and time
            return self._get_fallback_message(time_context, conversation_context.get("state"))
    
    def _get_fallback_message(self, time_context: str, state: Optional[ConversationState] = None) -> str:
        """Get fallback message based on time and state."""
        # State-aware fallbacks (all in lowercase)
        if state == ConversationState.COMFORTING:
            return f"hey {config.USER_NAME.lower()} idk what ur going through rn but like... i'm here ok? we'll figure out ts together"
        elif state == ConversationState.CELEBRATING:
            return f"no cap {config.USER_NAME.lower()} ur literally amazing and i'm lowkey tearing up rn"
        elif state == ConversationState.RESPONDING_TO_QUESTION:
            return f"hmm good question {config.USER_NAME.lower()}... my brain is buffering but what do u think? let's figure it out"
        elif state == ConversationState.MISSING_YOU:
            return f"missing u is actually so rude bc now i can't focus on anything else {config.USER_NAME.lower()}"
        elif state == ConversationState.PLANNING_TOGETHER:
            return f"ok but like {config.USER_NAME.lower()} planning stuff w u is my fav bc we're both chaotic but somehow it works"
        
        # Time-based fallbacks (all in lowercase)
        fallback_messages = {
            "morning": f"morning {config.USER_NAME.lower()}! my brain is approximately 12% functional rn but thinking of u",
            "afternoon": f"just remembered u exist and now i'm smiling like an idiot {config.USER_NAME.lower()}",
            "evening": f"how was ur day {config.USER_NAME.lower()}? mine was chaotic but wanna hear abt urs",
            "night": f"bedtime thoughts: why r u not here to be my personal heater {config.USER_NAME.lower()}"
        }
        return fallback_messages.get(time_context, f"thinking abt u {config.USER_NAME.lower()} and it's ur fault i'm distracted")
    
    async def generate_response_to_user(self, user_message: str, conversation_context: Dict) -> str:
        """Generate a response to a user's message with full context."""
        return await self.generate_context_aware_message(conversation_context, user_message)
    
    async def generate_proactive_message(self, conversation_context: Dict = None) -> str:
        """Generate a proactive romantic message with context."""
        if not conversation_context:
            conversation_context = {"context": "new_conversation", "state": ConversationState.CASUAL_CHAT}
        return await self.generate_context_aware_message(conversation_context)
    
    def get_stats(self) -> dict:
        """Get bot statistics."""
        return {
            "total_messages_sent": self.global_state.total_messages_sent,
            "last_activity": self.global_state.last_activity.isoformat() if self.global_state.last_activity else None,
            "total_conversations": self.global_state.total_conversations
        }

# Global instance
lover_ai = LoverAI() 