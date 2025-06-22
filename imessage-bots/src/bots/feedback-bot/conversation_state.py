from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
import re
import random
import hashlib
from models import (
    FeedbackConversation, ConversationState, FeedbackBotState, 
    FeedbackType, StructuredFeedback, UserProfile, CrossChatInsight
)
from config import config

class FeedbackConversationManager:
    """Manages conversation state and feedback extraction for user interviews across multiple chats."""
    
    def __init__(self):
        # In-memory storage for conversation states
        # Key: chat_guid, Value: FeedbackConversation
        self._conversations: Dict[str, FeedbackConversation] = {}
        self._global_state = FeedbackBotState()
        self._global_state.active_chat_guids = config.CHAT_GUIDS.copy()
        
        # Mom Test probe questions for different feedback types
        self.mom_test_probes = {
            FeedbackType.FEATURE_REQUEST: [
                "What problem were you trying to solve when you realized you needed this feature?",
                "How do you currently handle this without the feature? What's your workaround?",
                "Can you walk me through the last time you faced this exact situation?",
                "What would happen if this feature didn't exist at all?",
                "How often do you run into this issue - daily, weekly, or just occasionally?"
            ],
            FeedbackType.BUG_REPORT: [
                "What were you trying to accomplish when this happened?",
                "How has this bug impacted your workflow or goals?",
                "What did you expect to happen instead?",
                "Is this something that happens every time or just sometimes?",
                "How did you end up working around this issue?"
            ],
            FeedbackType.PAIN_POINT: [
                "How long have you been dealing with this problem?",
                "What solutions have you tried before finding our product?",
                "How much time or money does this problem cost you?",
                "What would your life look like if this problem was completely solved?",
                "Who else is affected by this problem besides you?"
            ],
            FeedbackType.USAGE_PATTERN: [
                "What typically triggers you to use this feature?",
                "How does this fit into your broader workflow?",
                "What do you usually do right before and after using this?",
                "How did you discover this was possible?",
                "What would make this even more useful for you?"
            ],
            FeedbackType.GENERAL_FEEDBACK: [
                "What were you hoping to achieve when you first tried our product?",
                "How does this compare to what you were using before?",
                "What almost stopped you from trying us out?",
                "What would you tell a friend who's considering using this?",
                "What's the most important thing we could improve?"
            ]
        }
    
    def get_conversation(self, chat_guid: str) -> Optional[FeedbackConversation]:
        """Get conversation state for a chat."""
        return self._conversations.get(chat_guid)
    
    def get_all_conversations(self) -> Dict[str, FeedbackConversation]:
        """Get all conversations for cross-chat analysis."""
        return self._conversations.copy()
    
    def start_conversation(self, chat_guid: str) -> FeedbackConversation:
        """Start a new conversation or get existing one."""
        if chat_guid in self._conversations:
            return self._conversations[chat_guid]
        
        # Create new conversation with user profile
        user_profile = UserProfile(chat_guid=chat_guid)
        conversation = FeedbackConversation(
            chat_guid=chat_guid,
            state=ConversationState.INITIAL_CONTACT,
            user_profile=user_profile
        )
        self._conversations[chat_guid] = conversation
        self._global_state.total_conversations += 1
        return conversation
    
    def _generate_theme_from_feedback(self, feedback_type: FeedbackType, message: str) -> str:
        """Generate a privacy-safe theme from feedback without revealing specific details."""
        message_lower = message.lower()
        
        # Generate theme based on common patterns
        if feedback_type == FeedbackType.BUG_REPORT:
            if any(word in message_lower for word in ['payment', 'billing', 'charge', 'subscription']):
                return "payment_issues"
            elif any(word in message_lower for word in ['login', 'signup', 'account', 'password']):
                return "authentication_issues"
            elif any(word in message_lower for word in ['slow', 'loading', 'performance', 'speed']):
                return "performance_issues"
            elif any(word in message_lower for word in ['crash', 'freeze', 'error', 'broken']):
                return "stability_issues"
            else:
                return "general_bugs"
        
        elif feedback_type == FeedbackType.FEATURE_REQUEST:
            if any(word in message_lower for word in ['notification', 'alert', 'reminder']):
                return "notification_features"
            elif any(word in message_lower for word in ['search', 'find', 'filter']):
                return "search_features"
            elif any(word in message_lower for word in ['export', 'import', 'download', 'upload']):
                return "data_management"
            elif any(word in message_lower for word in ['mobile', 'app', 'phone']):
                return "mobile_features"
            else:
                return "general_features"
        
        elif feedback_type == FeedbackType.PAIN_POINT:
            if any(word in message_lower for word in ['confusing', 'complex', 'hard', 'difficult']):
                return "usability_confusion"
            elif any(word in message_lower for word in ['time', 'slow', 'manual', 'tedious']):
                return "efficiency_issues"
            elif any(word in message_lower for word in ['integration', 'connect', 'sync']):
                return "integration_problems"
            else:
                return "workflow_friction"
        
        # Default theme based on feedback type
        return f"{feedback_type.value}_general"
    
    def _update_cross_chat_insights(self, feedback: StructuredFeedback, chat_guid: str):
        """Update cross-chat insights based on new feedback, preserving privacy."""
        if not config.ENABLE_CROSS_CHAT_INSIGHTS:
            return
        
        theme = self._generate_theme_from_feedback(feedback.feedback_type, feedback.raw_message)
        
        if theme in self._global_state.cross_chat_insights:
            # Update existing insight
            insight = self._global_state.cross_chat_insights[theme]
            insight.frequency_count += 1
            insight.last_seen = datetime.now()
            
            # Check if this is from a new chat (without storing the specific GUID)
            chat_hash = hashlib.sha256(chat_guid.encode()).hexdigest()[:8]
            if chat_hash not in getattr(insight, '_chat_hashes', set()):
                insight.affected_chats += 1
                if not hasattr(insight, '_chat_hashes'):
                    insight._chat_hashes = set()
                insight._chat_hashes.add(chat_hash)
            
            # Update severity based on frequency and type
            if insight.frequency_count >= 5 or feedback.feedback_type in [FeedbackType.BUG_REPORT, FeedbackType.PAIN_POINT]:
                insight.severity_level = "high"
            elif insight.frequency_count >= 3:
                insight.severity_level = "medium"
        else:
            # Create new insight
            probes = self._generate_cross_chat_probes(theme, feedback.feedback_type)
            insight = CrossChatInsight(
                feedback_type=feedback.feedback_type,
                theme=theme,
                suggested_probes=probes,
                severity_level="high" if feedback.feedback_type in [FeedbackType.BUG_REPORT, FeedbackType.PAIN_POINT] else "medium"
            )
            # Track chat participation without storing actual GUID
            chat_hash = hashlib.sha256(chat_guid.encode()).hexdigest()[:8]
            insight._chat_hashes = {chat_hash}
            
            self._global_state.cross_chat_insights[theme] = insight
    
    def _generate_cross_chat_probes(self, theme: str, feedback_type: FeedbackType) -> List[str]:
        """Generate probes for cross-chat insights based on theme."""
        theme_probes = {
            "payment_issues": [
                "Have you noticed any patterns with when payment issues occur?",
                "What's your typical flow when making payments?",
                "How do you currently handle payment-related problems?"
            ],
            "authentication_issues": [
                "What's your usual process for logging in?",
                "How often do you find yourself having to reset things?",
                "What would make the login experience smoother for you?"
            ],
            "performance_issues": [
                "What time of day do you typically use the app?",
                "How does the speed compare to other similar tools you use?",
                "What's your internet setup like when you're using it?"
            ],
            "usability_confusion": [
                "What's the first thing you try when you get stuck?",
                "How do you usually figure out new features?",
                "What would make the interface more intuitive for you?"
            ],
            "notification_features": [
                "How do you prefer to be notified about things?",
                "What notifications do you find most useful in other apps?",
                "How often would you want to hear from us?"
            ],
            "search_features": [
                "What do you typically search for most often?",
                "How do you organize your information currently?",
                "What would make finding things faster for you?"
            ]
        }
        
        return theme_probes.get(theme, [
            "How often does this type of situation come up for you?",
            "What's your current workaround for this?",
            "How would solving this change your workflow?"
        ])
    
    def get_cross_chat_probe(self, chat_guid: str) -> Optional[str]:
        """Get a cross-chat insight probe for this chat if appropriate."""
        if not config.ENABLE_CROSS_CHAT_INSIGHTS:
            return None
        
        conversation = self.get_conversation(chat_guid)
        if not conversation:
            return None
        
        # Don't ask cross-chat probes too frequently
        if random.random() > config.CROSS_CHAT_PROBE_FREQUENCY:
            return None
        
        # Find insights that haven't been probed in this chat yet
        available_insights = []
        for theme, insight in self._global_state.cross_chat_insights.items():
            if (insight.affected_chats > 1 and  # Only probe if multiple chats are affected
                insight.severity_level in ["medium", "high"] and
                not any(probe in conversation.cross_chat_probes_asked for probe in insight.suggested_probes)):
                available_insights.append(insight)
        
        if not available_insights:
            return None
        
        # Select highest severity insight
        selected_insight = max(available_insights, key=lambda x: (x.severity_level == "high", x.frequency_count))
        
        # Get an unused probe
        available_probes = [probe for probe in selected_insight.suggested_probes 
                          if probe not in conversation.cross_chat_probes_asked]
        
        if available_probes:
            selected_probe = random.choice(available_probes)
            conversation.cross_chat_probes_asked.append(selected_probe)
            return selected_probe
        
        return None

    def analyze_feedback_type(self, message: str) -> FeedbackType:
        """Analyze message to determine feedback type."""
        message_lower = message.lower()
        
        # Bug report patterns
        bug_words = ['bug', 'broken', 'error', 'crash', 'doesn\'t work', 'not working', 'issue', 'problem', 'glitch', 'fail']
        if any(word in message_lower for word in bug_words):
            return FeedbackType.BUG_REPORT
        
        # Feature request patterns
        feature_words = ['feature', 'add', 'would love', 'wish', 'could you', 'suggestion', 'enhancement', 'improvement', 'missing']
        if any(word in message_lower for word in feature_words):
            return FeedbackType.FEATURE_REQUEST
        
        # Question patterns
        question_words = ['how', 'what', 'why', 'when', 'where', 'who', 'which', 'can', 'could', 'would', 'should']
        if any(word in message_lower for word in question_words) or message.endswith('?'):
            return FeedbackType.QUESTION
        
        # Complaint patterns
        complaint_words = ['hate', 'annoying', 'frustrated', 'difficult', 'hard', 'confusing', 'slow', 'bad']
        if any(word in message_lower for word in complaint_words):
            return FeedbackType.COMPLAINT
        
        # Praise patterns
        praise_words = ['love', 'great', 'awesome', 'amazing', 'fantastic', 'helpful', 'useful', 'perfect', 'excellent']
        if any(word in message_lower for word in praise_words):
            return FeedbackType.PRAISE
        
        # Usage pattern indicators
        usage_words = ['use', 'using', 'workflow', 'process', 'routine', 'usually', 'always', 'typically']
        if any(word in message_lower for word in usage_words):
            return FeedbackType.USAGE_PATTERN
        
        return FeedbackType.GENERAL_FEEDBACK
    
    def extract_structured_feedback(self, message: str, feedback_type: FeedbackType) -> StructuredFeedback:
        """Extract structured feedback from user message."""
        return StructuredFeedback(
            feedback_type=feedback_type,
            summary=message[:200] + "..." if len(message) > 200 else message,
            raw_message=message,
            context={"analyzed_at": datetime.now().isoformat()}
        )
    
    def generate_mom_test_probe(self, feedback: StructuredFeedback, conversation: FeedbackConversation) -> Optional[str]:
        """Generate a Mom Test probe question based on the feedback."""
        probes = self.mom_test_probes.get(feedback.feedback_type, self.mom_test_probes[FeedbackType.GENERAL_FEEDBACK])
        
        # Filter out probes we've already asked
        available_probes = [probe for probe in probes if probe not in conversation.pending_probes]
        
        if not available_probes:
            return None
        
        # Return the first available probe
        selected_probe = available_probes[0]
        conversation.pending_probes.append(selected_probe)
        return selected_probe
    
    def process_user_message(self, chat_guid: str, message: str) -> FeedbackConversation:
        """Process a user message and update conversation context."""
        conversation = self.start_conversation(chat_guid)
        
        # Analyze feedback type
        feedback_type = self.analyze_feedback_type(message)
        
        # Add user message to conversation
        conversation.add_user_message(message, feedback_type)
        
        # Extract structured feedback if this contains feedback
        if feedback_type != FeedbackType.QUESTION:
            structured_feedback = self.extract_structured_feedback(message, feedback_type)
            conversation.current_feedback = structured_feedback
            conversation.total_feedback_collected += 1
            
            # Update cross-chat insights
            self._update_cross_chat_insights(structured_feedback, chat_guid)
            
            # Update user profile
            conversation.user_profile.total_feedback_items += 1
            if feedback_type.value not in conversation.user_profile.feedback_types:
                conversation.user_profile.feedback_types[feedback_type.value] = 0
            conversation.user_profile.feedback_types[feedback_type.value] += 1
            
            # Update global stats
            self._global_state.total_feedback_items += 1
            if feedback_type.value not in self._global_state.feedback_by_type:
                self._global_state.feedback_by_type[feedback_type.value] = 0
            self._global_state.feedback_by_type[feedback_type.value] += 1
        
        # Update conversation state based on feedback
        if conversation.state == ConversationState.INITIAL_CONTACT:
            conversation.state = ConversationState.COLLECTING_FEEDBACK
        elif conversation.state == ConversationState.COLLECTING_FEEDBACK and feedback_type != FeedbackType.QUESTION:
            conversation.state = ConversationState.PROBING_DEEPER
        elif conversation.state == ConversationState.PROBING_DEEPER:
            # Check if we should move to summarizing instead of more probing
            if conversation.total_questions_asked >= 3 or self._has_sufficient_detail(conversation):
                conversation.state = ConversationState.SUMMARIZING
        
        return conversation
    
    def should_probe_deeper(self, conversation: FeedbackConversation) -> bool:
        """Determine if we should ask a Mom Test probe question."""
        # Never ask more than 3 questions total in a session
        if conversation.total_questions_asked >= 3:
            return False
        
        # Don't probe if we don't have feedback to probe about
        if not conversation.current_feedback:
            return False
            
        # Check if we have enough detail already
        if self._has_sufficient_detail(conversation):
            return False
        
        return conversation.state == ConversationState.PROBING_DEEPER
    
    def _has_sufficient_detail(self, conversation: FeedbackConversation) -> bool:
        """Check if we have sufficient detail to stop probing."""
        if not conversation.current_feedback:
            return False
            
        # For bug reports, we want: what happened, what they were trying to do, device/context
        if conversation.current_feedback.feedback_type == FeedbackType.BUG_REPORT:
            recent_messages = [msg.content.lower() for msg in conversation.conversation_history[-6:] if msg.role == "user"]
            
            # Check if we have the essential details
            has_what_happened = any("when" in msg or "pressed" in msg or "clicked" in msg or "tried" in msg for msg in recent_messages)
            has_context = any("iphone" in msg or "android" in msg or "mobile" in msg or "wifi" in msg or "data" in msg for msg in recent_messages)
            has_action = any("trying to" in msg or "wanted to" in msg or "ordering" in msg or "using" in msg for msg in recent_messages)
            
            return has_what_happened and (has_context or has_action)
        
        # For other feedback types, be more conservative - stop after fewer questions
        return conversation.total_questions_asked >= 2
    
    def should_summarize(self, conversation: FeedbackConversation) -> bool:
        """Determine if we should summarize the feedback collected so far."""
        return (
            conversation.total_questions_asked >= 3 or 
            (conversation.total_questions_asked >= 2 and self._has_sufficient_detail(conversation))
        )
    
    def is_session_ending(self, conversation: FeedbackConversation) -> bool:
        """Determine if this feedback session is ending and should trigger Linear issue creation."""
        return (
            conversation.state == ConversationState.SUMMARIZING or
            conversation.state == ConversationState.THANKING or
            (conversation.total_questions_asked >= config.MAX_QUESTIONS_PER_SESSION and
             conversation.total_feedback_collected > 0)
        )
    
    def collect_feedback_for_chat(self, chat_guid: str) -> Dict:
        """Collect all feedback from a specific chat conversation for Linear triaging."""
        conversation = self.get_conversation(chat_guid)
        if not conversation:
            return {
                "feedback_items": [],
                "chat_guid": chat_guid,
                "total_feedback": 0
            }
        
        feedback_items = []
        
        # Collect structured feedback from conversation history
        for message in conversation.conversation_history:
            if message.role == "user" and message.feedback_type:
                # Create structured feedback for this message
                structured_feedback = self.extract_structured_feedback(
                    message.content, 
                    message.feedback_type
                )
                structured_feedback.timestamp = message.timestamp
                
                # Add conversation context
                chat_info = {
                    "chat_guid": chat_guid,  # This will be anonymized in the triager
                    "total_questions": conversation.total_questions_asked,
                    "conversation_length": len(conversation.conversation_history),
                    "session_state": conversation.state.value,
                    "user_profile": {
                        "engagement_level": conversation.user_profile.engagement_level,
                        "total_feedback_items": conversation.user_profile.total_feedback_items,
                        "feedback_types": conversation.user_profile.feedback_types
                    }
                }
                
                feedback_items.append({
                    "feedback": structured_feedback,
                    "chat_info": chat_info
                })
        
        # Also include current feedback if it exists
        if conversation.current_feedback:
            chat_info = {
                "chat_guid": chat_guid,
                "total_questions": conversation.total_questions_asked,
                "conversation_length": len(conversation.conversation_history),
                "session_state": conversation.state.value,
                "user_profile": {
                    "engagement_level": conversation.user_profile.engagement_level,
                    "total_feedback_items": conversation.user_profile.total_feedback_items,
                    "feedback_types": conversation.user_profile.feedback_types
                }
            }
            
            feedback_items.append({
                "feedback": conversation.current_feedback,
                "chat_info": chat_info
            })
        
        return {
            "feedback_items": feedback_items,
            "chat_guid": chat_guid,
            "total_feedback": len(feedback_items),
            "session_state": conversation.state.value,
            "total_questions_asked": conversation.total_questions_asked,
            "collection_timestamp": datetime.now().isoformat()
        }
    
    def mark_session_triaged(self, chat_guid: str):
        """Mark that a session's feedback has been triaged to Linear."""
        conversation = self.get_conversation(chat_guid)
        if conversation:
            # Add a flag to track that this session was triaged
            if not hasattr(conversation, '_triaged_to_linear'):
                conversation._triaged_to_linear = True
                conversation._triaged_timestamp = datetime.now()
    
    def get_conversation_context(self, chat_guid: str) -> Dict:
        """Get comprehensive conversation context for AI generation."""
        conversation = self.get_conversation(chat_guid)
        if not conversation:
            return {
                "context": "new_conversation", 
                "state": ConversationState.INITIAL_CONTACT,
                "total_feedback": 0
            }
        
        recent_messages = conversation.conversation_history[-5:] if conversation.conversation_history else []
        
        # Get potential cross-chat probe
        cross_chat_probe = self.get_cross_chat_probe(chat_guid)
        
        context = {
            "state": conversation.state,
            "current_feedback_type": conversation.current_feedback.feedback_type.value if conversation.current_feedback else None,
            "total_feedback_collected": conversation.total_feedback_collected,
            "total_questions_asked": conversation.total_questions_asked,
            "user_profile": {
                "engagement_level": conversation.user_profile.engagement_level,
                "feedback_types": conversation.user_profile.feedback_types,
                "total_feedback_items": conversation.user_profile.total_feedback_items
            },
            "recent_messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "feedback_type": msg.feedback_type.value if msg.feedback_type else None,
                    "timestamp": msg.timestamp.isoformat()
                }
                for msg in recent_messages
            ],
            "should_probe": self.should_probe_deeper(conversation),
            "should_summarize": self.should_summarize(conversation),
            "cross_chat_probe": cross_chat_probe,
            "pending_probes_count": len(conversation.pending_probes),
            "last_interaction": conversation.last_interaction.isoformat()
        }
        
        return context
    
    def mark_message_sent(self, chat_guid: str, message: str):
        """Mark that a message was sent in the conversation."""
        conversation = self.get_conversation(chat_guid)
        if conversation:
            conversation.add_bot_message(message)
            if self._is_question(message):
                conversation.total_questions_asked += 1
        
        # Update global state
        self._global_state.last_activity = datetime.now()
    
    def _is_question(self, message: str) -> bool:
        """Check if a message is a question."""
        question_indicators = ['?', 'how', 'what', 'why', 'when', 'where', 'who', 'which', 'can you', 'could you', 'would you']
        message_lower = message.lower()
        return any(indicator in message_lower for indicator in question_indicators)
    
    def get_stats(self) -> Dict:
        """Get comprehensive statistics for all conversations."""
        active_conversations = sum(1 for conv in self._conversations.values() 
                                 if conv.last_interaction > datetime.now() - timedelta(hours=24))
        
        conversation_states = {}
        for conv in self._conversations.values():
            state = conv.state.value
            conversation_states[state] = conversation_states.get(state, 0) + 1
        
        return {
            "total_conversations": self._global_state.total_conversations,
            "active_conversations": active_conversations,
            "total_feedback_items": self._global_state.total_feedback_items,
            "feedback_by_type": self._global_state.feedback_by_type,
            "conversation_states": conversation_states,
            "cross_chat_insights": {
                theme: {
                    "frequency": insight.frequency_count,
                    "affected_chats": insight.affected_chats,
                    "severity": insight.severity_level,
                    "theme": insight.theme
                }
                for theme, insight in self._global_state.cross_chat_insights.items()
            },
            "monitored_chats": len(self._global_state.active_chat_guids),
            "last_activity": self._global_state.last_activity.isoformat() if self._global_state.last_activity else None
        }
    
    def collect_all_feedback_for_triaging(self) -> Dict:
        """Collect all feedback from all conversations for Linear triaging."""
        feedback_items = []
        
        for chat_guid, conversation in self._conversations.items():
            # Collect structured feedback from conversation history
            for message in conversation.conversation_history:
                if message.role == "user" and message.feedback_type:
                    # Create structured feedback for this message
                    structured_feedback = self.extract_structured_feedback(
                        message.content, 
                        message.feedback_type
                    )
                    structured_feedback.timestamp = message.timestamp
                    
                    # Add conversation context
                    chat_info = {
                        "chat_guid": chat_guid,  # This will be anonymized in the triager
                        "total_questions": conversation.total_questions_asked,
                        "conversation_length": len(conversation.conversation_history),
                        "user_profile": {
                            "engagement_level": conversation.user_profile.engagement_level,
                            "total_feedback_items": conversation.user_profile.total_feedback_items,
                            "feedback_types": conversation.user_profile.feedback_types
                        }
                    }
                    
                    feedback_items.append({
                        "feedback": structured_feedback,
                        "chat_info": chat_info
                    })
            
            # Also include current feedback if it exists
            if conversation.current_feedback:
                chat_info = {
                    "chat_guid": chat_guid,
                    "total_questions": conversation.total_questions_asked,
                    "conversation_length": len(conversation.conversation_history),
                    "user_profile": {
                        "engagement_level": conversation.user_profile.engagement_level,
                        "total_feedback_items": conversation.user_profile.total_feedback_items,
                        "feedback_types": conversation.user_profile.feedback_types
                    }
                }
                
                feedback_items.append({
                    "feedback": conversation.current_feedback,
                    "chat_info": chat_info
                })
        
        return {
            "feedback_items": feedback_items,
            "cross_chat_insights": self._global_state.cross_chat_insights,
            "total_conversations": len(self._conversations),
            "collection_timestamp": datetime.now().isoformat()
        }
    
    def clear_triaged_feedback(self) -> None:
        """Clear feedback that has been triaged (optional - for cleanup)."""
        # This is optional - you might want to keep feedback for analysis
        # For now, we'll just reset counters but keep the conversations
        for conversation in self._conversations.values():
            conversation.total_feedback_collected = 0
            # Keep conversation history but could optionally archive it
        
        # Reset global counters
        self._global_state.total_feedback_items = 0
        self._global_state.feedback_by_type = {}

# Global conversation manager instance
conversation_manager = FeedbackConversationManager() 