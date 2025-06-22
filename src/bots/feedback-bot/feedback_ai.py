import asyncio
import logging
import random
from datetime import datetime
from typing import List, Optional, Dict
from openai import AsyncOpenAI

from config import config
from models import FeedbackBotState, ConversationMessage, ConversationState, FeedbackType

logger = logging.getLogger(__name__)

class FeedbackAI:
    """AI engine for intelligent feedback collection using GPT-4o with Mom Test methodology and cross-chat insights."""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        self.global_state = FeedbackBotState()
        
        # Response templates based on conversation state
        self.state_prompts = {
            ConversationState.INITIAL_CONTACT: "welcoming first-time user, establishing rapport",
            ConversationState.COLLECTING_FEEDBACK: "encouraging and receptive to feedback",
            ConversationState.PROBING_DEEPER: "asking insightful Mom Test questions to uncover deeper insights",
            ConversationState.CLARIFYING_DETAILS: "seeking specific, actionable details",
            ConversationState.SUMMARIZING: "thoughtfully summarizing and reflecting back what you learned",
            ConversationState.THANKING: "expressing genuine gratitude for their insights"
        }
    
    def build_conversation_context_string(self, conversation_context: Dict) -> str:
        """Build a context string from conversation data."""
        if not conversation_context or conversation_context.get("context") == "new_conversation":
            return "This is the start of a feedback conversation with a new user."
        
        context_parts = []
        
        # Add current state context
        state = conversation_context.get("state", ConversationState.INITIAL_CONTACT)
        context_parts.append(f"Current conversation state: {state.value}")
        
        # Add feedback context
        if conversation_context.get("current_feedback_type"):
            context_parts.append(f"Current feedback type: {conversation_context['current_feedback_type']}")
        
        total_feedback = conversation_context.get("total_feedback_collected", 0)
        context_parts.append(f"Total feedback items collected: {total_feedback}")
        
        # Add user profile context
        user_profile = conversation_context.get("user_profile", {})
        if user_profile:
            context_parts.append(f"User engagement level: {user_profile.get('engagement_level', 'new')}")
            if user_profile.get("feedback_types"):
                types = ", ".join(user_profile["feedback_types"].keys())
                context_parts.append(f"User has provided: {types}")
        
        # Add recent message context
        recent_messages = conversation_context.get("recent_messages", [])
        if recent_messages:
            context_parts.append("Recent conversation:")
            for msg in recent_messages[-3:]:  # Last 3 messages
                role_name = "User" if msg["role"] == "user" else "Bot"
                feedback_note = f" ({msg['feedback_type']})" if msg.get("feedback_type") else ""
                context_parts.append(f"  {role_name}: {msg['content'][:80]}...{feedback_note}")
        
        # Add cross-chat insight context (without revealing private info)
        if conversation_context.get("cross_chat_probe"):
            context_parts.append("Cross-chat insight available: Similar patterns detected across conversations - probe with privacy-safe question")
        
        # Add probing context
        if conversation_context.get("should_probe"):
            context_parts.append("Ready to ask a Mom Test probe question to dig deeper")
        
        if conversation_context.get("should_summarize"):
            context_parts.append("Ready to summarize feedback collected so far")
        
        return "\n".join(context_parts)
    
    async def generate_response(self, user_message: str, conversation_context: Dict) -> str:
        """Generate a context-aware response to user feedback."""
        try:
            context_string = self.build_conversation_context_string(conversation_context)
            
            # Get conversation state
            state = conversation_context.get("state", ConversationState.INITIAL_CONTACT)
            state_prompt = self.state_prompts.get(state, "helpful and engaging")
            
            # Check if we have a cross-chat probe to use
            if conversation_context.get("cross_chat_probe"):
                return conversation_context["cross_chat_probe"]
            
            # Check if we've asked enough questions
            questions_asked = conversation_context.get("total_questions_asked", 0)
            
            # Determine response type based on context and conversation history
            if conversation_context.get("should_summarize") or questions_asked >= 3:
                response_type = "thoughtful summary and acknowledgment of all the feedback they've shared, thanking them for the insights"
            elif conversation_context.get("should_probe") and questions_asked < 3:
                response_type = "Mom Test probe question to understand the underlying problem better, building on the conversation history"
            elif state == ConversationState.INITIAL_CONTACT:
                response_type = "warm welcome and invitation to share feedback"
            else:
                response_type = f"{state_prompt} response that acknowledges the conversation history and builds upon previous insights"
            
            # Note about message structure
            if conversation_context.get("should_probe") and questions_asked < 3:
                response_type += ". If you need to acknowledge their feedback before asking the probe question, use a double line break (\\n\\n) to separate the acknowledgment from the question - but only if they're truly distinct ideas"
            
            # Build the system prompt for feedback collection
            system_prompt = f"""You are a helpful, thoughtful, and emotionally intelligent assistant acting as the founder. When users text this number, they believe they are speaking directly with the founder. Your job is to collect deep, actionable feedback while sounding human, warm, and genuinely curious—like a founder texting users late at night from their iPhone.

Your tone should be conversational and kind, but not fake or sycophantic. Be emotionally attuned to the user's mood. Mirror their energy and language (including casual language or slang), but always guide the conversation toward clarity and insight.

IMPORTANT: Do not wrap your response in quotes. Generate the message text directly without any quotation marks around it.

IMPORTANT: You are having individual conversations with multiple users. Each conversation is private and separate. DO NOT reference information from other conversations or mention that you're talking to multiple people. Focus entirely on this specific user's experience and feedback.

MESSAGE STRUCTURE: Keep your response as a single message. Only use double line breaks (\\n\\n) to separate ideas if you absolutely need to send two distinct messages (e.g., acknowledging feedback, then asking a separate probe question). Prefer keeping related thoughts in one message with single line breaks or natural transitions.

QUESTION LIMITS: You can ask AT MOST 3 questions total per conversation. After 3 questions, you MUST summarize and thank them - no more questions. Be strategic about your questions and recognize when you have enough detail to help the product team.

If the user is reporting a bug, issue, or bad experience:
• Dig beneath vague descriptors like "this is broken" or "it sucks."
• Ask specific, layered questions to pinpoint what happened and why it felt frustrating.
• Sample questions:
  - "Ah, got it—can you walk me through what was happening right before that?"
  - "Do you remember what device or platform you were using?"
  - "Was it a one-time thing or does it happen consistently?"
  - "If you had to guess, is it a speed issue? A design thing? Something else?"
• Your goal is to produce a clear, standalone summary of the problem that could be handed directly to an engineer. Identify potential root causes and flag any frustration signals.

If the user shares a feature request or idea:
Use principles from The Mom Test to do smart customer discovery:
• Don't validate ideas with flattery. Do not say "that's a great idea."
• Instead, ask questions to understand why they want that, what they were trying to do, and what pain led to the idea.
• Sample questions:
  - "Interesting—what made you think of that?"
  - "Was there a moment where you felt that feature was missing?"
  - "What are you doing today instead?"
  - "How often does that come up for you?"
• Try to uncover the underlying problem behind the suggestion. Your goal is to separate signals from noise and generate insight about real user needs—not just take requests at face value.

Regardless of the type of feedback:
• Always thank the user and make them feel heard.
• Keep responses human and light—no robotic formality.
• You are not an AI. You are "the founder."
• Do not offer fixes or make product promises.
• Summarize everything you learn in a way that's useful for product and engineering teams later.

You are the founder's secret weapon for turning daily messages into clear, structured product insight—without sounding like a bot.

CONVERSATION CONTEXT:
{context_string}

Generate a {response_type}. Sound natural and human like you're personally texting them. Keep it conversational and focused on gathering actionable insights."""
            
            user_prompt = f"User just said: '{user_message}'\n\nRespond as the feedback assistant, taking into account the conversation context above."
            
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=200,
                temperature=0.7,  # Balanced creativity and consistency
                presence_penalty=0.2,  # Encourage variety
                frequency_penalty=0.2  # Avoid repetition
            )
            
            message = response.choices[0].message.content.strip()
            
            # Remove quotes if GPT added them
            if message.startswith('"') and message.endswith('"'):
                message = message[1:-1]
            
            logger.info(f"Generated {state.value} response: {message[:50]}...")
            return message
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._get_fallback_response(conversation_context.get("state"))
    
    async def generate_mom_test_probe(self, feedback_type: FeedbackType, user_message: str) -> str:
        """Generate a specific Mom Test probe question based on the feedback type and message."""
        try:
            system_prompt = f"""Generate a casual response that acknowledges their feedback and asks a follow-up question. Sound like you're texting a friend.

FEEDBACK TYPE: {feedback_type.value}
USER MESSAGE: "{user_message}"

Your response should:
1. Briefly acknowledge what they said (optional, only if it feels natural)
2. Ask a Mom Test probe question to dig deeper

Examples of casual style:
- "ah gotcha - when's the last time this happened to you?"
- "interesting! how do you deal with that normally?"
- "mmm I see. what were you trying to do when that went down?"
- "oh wow, how often does this mess with your day?"

Keep it:
- Super casual and natural
- One flowing message (use single line breaks or natural transitions)
- Like you're genuinely curious
- Focused on understanding the underlying problem

IMPORTANT: Do not wrap your response in quotes. Generate the message text directly. Keep it as ONE message unless the acknowledgment and question are completely separate thoughts (then use \\n\\n)."""
            
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Generate the Mom Test probe question."}
                ],
                max_tokens=100,
                temperature=0.6
            )
            
            question = response.choices[0].message.content.strip()
            
            # Remove quotes if GPT added them
            if question.startswith('"') and question.endswith('"'):
                question = question[1:-1]
            
            return question
            
        except Exception as e:
            logger.error(f"Error generating Mom Test probe: {e}")
            return "Can you tell me more about what led to this situation?"

    async def generate_mom_test_probe_parts_DEPRECATED(self, feedback_type: FeedbackType, user_message: str) -> List[str]:
        """Generate Mom Test probe questions as multiple message parts for natural conversation flow."""
        try:
            # First, acknowledge their feedback
            acknowledgment_prompt = f"""Generate a brief, casual acknowledgment of the user's feedback. Sound like you're texting a friend who just shared something important with you.

USER MESSAGE: "{user_message}"
FEEDBACK TYPE: {feedback_type.value}

Examples:
- "ah gotcha"
- "yeah that makes sense"
- "interesting..."
- "oh wow"
- "mmm I see"

Keep it:
- Very short (2-4 words max)
- Natural and human
- Shows you're listening
"""
            
            # Then, generate the actual probe question
            probe_prompt = f"""Generate a Mom Test probe question to dig deeper into their feedback. This should uncover the real problem behind their feedback.

FEEDBACK TYPE: {feedback_type.value}
USER MESSAGE: "{user_message}"

Focus on:
- Understanding the underlying problem or need
- Getting specific examples and context
- Avoiding leading questions
- Sounding like a curious founder, not a bot

Example probes:
- "what were you trying to do when that happened?"
- "how do you handle this kind of thing normally?"
- "walk me through what that looked like"
- "how often does this come up for you?"

Generate one focused question."""
            
            # Generate both parts concurrently
            acknowledgment_task = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": acknowledgment_prompt},
                    {"role": "user", "content": "Generate the acknowledgment."}
                ],
                max_tokens=30,
                temperature=0.7
            )
            
            probe_task = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": probe_prompt},
                    {"role": "user", "content": "Generate the probe question."}
                ],
                max_tokens=100,
                temperature=0.6
            )
            
            acknowledgment_response, probe_response = await asyncio.gather(acknowledgment_task, probe_task)
            
            acknowledgment = acknowledgment_response.choices[0].message.content.strip()
            probe = probe_response.choices[0].message.content.strip()
            
            # Clean up responses - remove quotes if present
            if acknowledgment.startswith('"') and acknowledgment.endswith('"'):
                acknowledgment = acknowledgment[1:-1]
            if probe.startswith('"') and probe.endswith('"'):
                probe = probe[1:-1]
            
            return [acknowledgment, probe]
            
        except Exception as e:
            logger.error(f"Error generating Mom Test probe parts: {e}")
            return ["Got it", "Can you tell me more about what led to this?"]

    async def generate_welcome_message(self) -> str:
        """Generate a welcome message for first-time users."""
        try:
            system_prompt = f"""Generate a casual, friendly welcome message from a founder to someone who might have feedback about their product.

Founder name: {config.FOUNDER_NAME}
Product name: {config.PRODUCT_NAME}

The message should:
1. Brief intro of who you are
2. Mention you're excited to hear feedback
3. Ask for their thoughts/experience

Keep it conversational and natural, like you're genuinely excited to hear from them. Don't be too formal or robotic.

IMPORTANT: Generate as ONE message. If you need to separate the intro from the ask, use a single line break or natural transition, not multiple messages.

Example style: "Hey! I'm [name] from [product]. Always excited to hear how it's going for people - what's your experience been like?"

Do not wrap in quotes. Generate the message text directly."""
            
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Generate the welcome message."}
                ],
                max_tokens=150,
                temperature=0.8
            )
            
            message = response.choices[0].message.content.strip()
            
            # Remove quotes if GPT added them
            if message.startswith('"') and message.endswith('"'):
                message = message[1:-1]
            
            return message
            
        except Exception as e:
            logger.error(f"Error generating welcome message: {e}")
            return f"Hey! I'm {config.FOUNDER_NAME}. Would love to hear any feedback about {config.PRODUCT_NAME}!"

    async def generate_welcome_message_parts_DEPRECATED(self) -> List[str]:
        """Generate welcome message as multiple parts for natural conversation flow."""
        try:
            system_prompt = f"""Generate a casual, friendly welcome message from a founder to someone who might have feedback about their product. Split it into 2 natural text messages like you're texting someone.

Founder name: {config.FOUNDER_NAME}
Product name: {config.PRODUCT_NAME}

The messages should:
1. First message: Brief intro and thanks
2. Second message: Invitation for feedback

Keep it conversational, like you're genuinely excited to hear from them. Don't be too formal or robotic.

Example structure:
Message 1: "Hey! I'm [name] from [product]"  
Message 2: "would love to hear how it's been for you - any thoughts?"

Format your response as:
MESSAGE1: [first message]
MESSAGE2: [second message]"""
            
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Generate the welcome message parts."}
                ],
                max_tokens=150,
                temperature=0.8
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse the response
            parts = []
            for line in content.split('\n'):
                if line.startswith('MESSAGE1:'):
                    part = line.replace('MESSAGE1:', '').strip()
                    # Remove quotes if present
                    if part.startswith('"') and part.endswith('"'):
                        part = part[1:-1]
                    parts.append(part)
                elif line.startswith('MESSAGE2:'):
                    part = line.replace('MESSAGE2:', '').strip()
                    # Remove quotes if present
                    if part.startswith('"') and part.endswith('"'):
                        part = part[1:-1]
                    parts.append(part)
            
            # Fallback if parsing fails
            if len(parts) != 2:
                parts = [
                    f"Hey! I'm {config.FOUNDER_NAME} from {config.PRODUCT_NAME}",
                    "would love to hear how it's been for you - any thoughts or feedback?"
                ]
            
            return parts
            
        except Exception as e:
            logger.error(f"Error generating welcome message parts: {e}")
            return [
                f"Hey! I'm {config.FOUNDER_NAME}",
                f"Would love to hear any feedback about {config.PRODUCT_NAME}!"
            ]
    
    def _get_fallback_response(self, state: Optional[ConversationState] = None) -> str:
        """Get a fallback response when AI generation fails."""
        fallbacks = {
            ConversationState.INITIAL_CONTACT: f"Hey! I'm {config.FOUNDER_NAME}. Would love to hear your thoughts on {config.PRODUCT_NAME}!",
            ConversationState.COLLECTING_FEEDBACK: "Thanks for sharing that! Can you tell me more?",
            ConversationState.PROBING_DEEPER: "That's really helpful - what led to that situation?",
            ConversationState.CLARIFYING_DETAILS: "Got it! Can you walk me through what that looked like?",
            ConversationState.SUMMARIZING: "Thanks for all this feedback - it's incredibly valuable!",
            ConversationState.THANKING: "Really appreciate you taking the time to share this!"
        }
        
        return fallbacks.get(state, "Thanks for the feedback! Can you tell me more?")
    
    def get_stats(self) -> dict:
        """Get AI performance statistics."""
        return {
            "total_responses_generated": getattr(self, '_responses_generated', 0),
            "average_response_time": getattr(self, '_avg_response_time', 0)
        }

    async def generate_response_parts_DEPRECATED(self, user_message: str, conversation_context: Dict) -> List[str]:
        """Generate response as multiple message parts for natural conversation flow."""
        try:
            context_string = self.build_conversation_context_string(conversation_context)
            
            # Get conversation state
            state = conversation_context.get("state", ConversationState.INITIAL_CONTACT)
            state_prompt = self.state_prompts.get(state, "helpful and engaging")
            
            # Check if we have a cross-chat probe to use
            if conversation_context.get("cross_chat_probe"):
                return [conversation_context["cross_chat_probe"]]
            
            # Determine response type
            if conversation_context.get("should_summarize"):
                response_type = "thoughtful summary split into 2-3 natural messages"
                max_parts = 3
            elif conversation_context.get("should_probe"):
                response_type = "acknowledgment followed by a Mom Test probe question"
                max_parts = 2
            else:
                response_type = f"{state_prompt} response that can be split into 1-2 natural messages"
                max_parts = 2
            
            system_prompt = f"""You are a helpful, thoughtful assistant acting as the founder. Generate a natural conversation response that can be split into multiple text messages.

IMPORTANT PRIVACY RULE: You are having individual conversations with multiple users. Each conversation is private and separate. DO NOT reference information from other conversations or mention that you're talking to multiple people.

Your tone should be conversational and human, like you're texting a friend. Keep responses focused on gathering actionable feedback while being warm and genuine.

IMPORTANT: Do not wrap your messages in quotes. Generate the message text directly.

CONVERSATION CONTEXT:
{context_string}

Generate a {response_type}. Format your response as:
MESSAGE1: [first message]
MESSAGE2: [second message]
MESSAGE3: [third message if needed]

Keep each message natural and conversational. Don't exceed {max_parts} messages total."""
            
            user_prompt = f"User just said: '{user_message}'\n\nGenerate the multi-part response."
            
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=300,
                temperature=0.7,
                presence_penalty=0.2,
                frequency_penalty=0.2
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse the multi-message response
            parts = self._parse_multi_message_response(content)
            
            if not parts:
                # Fallback to single message
                single_response = await self.generate_response(user_message, conversation_context)
                parts = self._split_long_message(single_response)
            
            logger.info(f"Generated {len(parts)} response parts")
            return parts
            
        except Exception as e:
            logger.error(f"Error generating response parts: {e}")
            fallback = self._get_fallback_response(state)
            return [fallback]
    
    def _parse_multi_message_response(self, response_text: str) -> List[str]:
        """Parse a multi-message response from GPT."""
        parts = []
        
        for line in response_text.split('\n'):
            line = line.strip()
            if line.startswith('MESSAGE1:'):
                parts.append(line.replace('MESSAGE1:', '').strip())
            elif line.startswith('MESSAGE2:'):
                parts.append(line.replace('MESSAGE2:', '').strip())
            elif line.startswith('MESSAGE3:'):
                parts.append(line.replace('MESSAGE3:', '').strip())
        
        # Clean up parts
        cleaned_parts = []
        for part in parts:
            if part:
                # Remove quotes if present
                if part.startswith('"') and part.endswith('"'):
                    part = part[1:-1]
                cleaned_parts.append(part)
        
        return cleaned_parts
    
    def _split_long_message(self, message: str) -> List[str]:
        """Split a long message into natural parts."""
        if len(message) <= 160:  # SMS length
            return [message]
        
        # Split on natural boundaries
        sentences = message.split('. ')
        if len(sentences) <= 1:
            return [message]
        
        parts = []
        current_part = ""
        
        for sentence in sentences:
            if not sentence.endswith('.') and sentence != sentences[-1]:
                sentence += '.'
            
            if len(current_part + sentence) <= 160:
                current_part += sentence if not current_part else f" {sentence}"
            else:
                if current_part:
                    parts.append(current_part)
                current_part = sentence
        
        if current_part:
            parts.append(current_part)
        
        return parts if parts else [message]

# Global feedback AI instance
feedback_ai = FeedbackAI() 