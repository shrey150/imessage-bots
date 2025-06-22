import asyncio
import logging
import requests
from typing import Dict, List, Optional, Any
from datetime import datetime
from openai import AsyncOpenAI

from config import config
from models import FeedbackType, StructuredFeedback, FeedbackConversation, CrossChatInsight

logger = logging.getLogger(__name__)

class LinearClient:
    """Client for interacting with Linear's GraphQL API to create issues from feedback."""
    
    def __init__(self):
        self.api_url = "https://api.linear.app/graphql"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": config.LINEAR_API_KEY
        }
        self.openai_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
        
    async def get_teams(self) -> List[Dict[str, Any]]:
        """Get all teams from Linear to find the target team ID."""
        query = """
        query Teams {
          teams {
            nodes {
              id
              name
              key
            }
          }
        }
        """
        
        try:
            response = requests.post(
                self.api_url,
                json={"query": query},
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            
            if "errors" in data:
                logger.error(f"Linear API errors: {data['errors']}")
                return []
                
            return data.get("data", {}).get("teams", {}).get("nodes", [])
            
        except Exception as e:
            logger.error(f"Error fetching teams from Linear: {e}")
            return []
    
    async def get_team_id(self) -> Optional[str]:
        """Get the team ID for the configured team."""
        teams = await self.get_teams()
        
        # If LINEAR_TEAM_KEY is specified, find by key
        if config.LINEAR_TEAM_KEY:
            for team in teams:
                if team.get("key") == config.LINEAR_TEAM_KEY:
                    return team["id"]
            logger.error(f"Team with key '{config.LINEAR_TEAM_KEY}' not found")
            return None
        
        # Otherwise, use the first team
        if teams:
            return teams[0]["id"]
        
        logger.error("No teams found in Linear")
        return None
    
    async def create_issue(self, title: str, description: str, team_id: str, 
                          priority: Optional[int] = None, 
                          labels: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Create a new Linear issue."""
        
        mutation = """
        mutation IssueCreate($input: IssueCreateInput!) {
          issueCreate(input: $input) {
            success
            issue {
              id
              identifier
              title
              url
            }
          }
        }
        """
        
        variables = {
            "input": {
                "teamId": team_id,
                "title": title,
                "description": description
            }
        }
        
        # Add priority if specified (1=Urgent, 2=High, 3=Normal, 4=Low)
        if priority:
            variables["input"]["priority"] = priority
        
        try:
            response = requests.post(
                self.api_url,
                json={"query": mutation, "variables": variables},
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            
            if "errors" in data:
                logger.error(f"Linear API errors: {data['errors']}")
                return None
            
            result = data.get("data", {}).get("issueCreate", {})
            if result.get("success"):
                return result.get("issue")
            else:
                logger.error(f"Failed to create Linear issue: {result}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating Linear issue: {e}")
            return None

class FeedbackTriager:
    """AI-powered feedback triager that converts feedback into Linear issues."""
    
    def __init__(self):
        self.linear_client = LinearClient()
        self.openai_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
    
    def _get_priority_from_feedback_type(self, feedback_type: FeedbackType, 
                                       severity: str = "medium") -> int:
        """Determine Linear priority based on feedback type and severity."""
        # Linear priorities: 1=Urgent, 2=High, 3=Normal, 4=Low
        
        if feedback_type == FeedbackType.BUG_REPORT:
            if severity == "high":
                return 1  # Urgent
            elif severity == "medium":
                return 2  # High
            else:
                return 3  # Normal
        
        elif feedback_type == FeedbackType.PAIN_POINT:
            if severity == "high":
                return 2  # High
            else:
                return 3  # Normal
        
        elif feedback_type == FeedbackType.FEATURE_REQUEST:
            if severity == "high":
                return 3  # Normal
            else:
                return 4  # Low
        
        else:
            return 3  # Normal (default)
    
    async def format_feedback_for_linear(self, 
                                       feedback_items: List[Dict[str, Any]], 
                                       cross_chat_insights: Dict[str, CrossChatInsight]) -> List[Dict[str, Any]]:
        """Use GPT-4o to format collected feedback into structured Linear issues."""
        
        # Prepare feedback summary for GPT-4o
        feedback_summary = self._prepare_feedback_summary(feedback_items, cross_chat_insights)
        
        system_prompt = f"""You are an expert product manager tasked with triaging user feedback into actionable Linear issues. 

You will receive a collection of feedback from users and need to:
1. Group related feedback together
2. Create clear, actionable issue titles and descriptions
3. Categorize feedback by type and priority
4. Format everything in structured markdown for Linear

FEEDBACK TYPES:
- Bug Report: Technical issues, crashes, errors
- Feature Request: New functionality users want
- Pain Point: Workflow problems, user frustration
- General Feedback: Overall product feedback

PRIORITY LEVELS:
- High: Critical bugs, major pain points affecting many users
- Medium: Important features, moderate bugs
- Low: Nice-to-have features, minor improvements

For each issue, provide:
- **Title**: Clear, concise summary (max 80 chars)
- **Description**: Detailed markdown with:
  - Problem statement
  - User impact
  - Relevant user quotes (anonymized)
  - Cross-chat insights if applicable
  - Suggested next steps
- **Type**: bug_report, feature_request, pain_point, or general_feedback
- **Priority**: high, medium, or low
- **Labels**: Relevant tags (max 3)

IMPORTANT: 
- Combine similar feedback into single issues
- Keep user information anonymous
- Focus on actionable insights
- Use markdown formatting for descriptions
- Be specific about the problem and impact

Return your response as a JSON array of issue objects."""

        user_prompt = f"""Here is the feedback collected from users:

{feedback_summary}

Please triage this feedback into Linear issues following the format specified. Group similar feedback together and focus on the most actionable insights."""

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=3000,
                temperature=0.3  # Lower temperature for more structured output
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Try to extract JSON from the response
            import json
            try:
                # Look for JSON array in the response
                start_idx = response_text.find('[')
                end_idx = response_text.rfind(']') + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx]
                    return json.loads(json_str)
                else:
                    # If no JSON array found, try to parse the whole response
                    return json.loads(response_text)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse GPT-4o response as JSON: {response_text}")
                return []
                
        except Exception as e:
            logger.error(f"Error formatting feedback with GPT-4o: {e}")
            return []
    
    def _prepare_feedback_summary(self, 
                                feedback_items: List[Dict[str, Any]], 
                                cross_chat_insights: Dict[str, CrossChatInsight]) -> str:
        """Prepare a summary of all feedback for GPT-4o processing."""
        summary_parts = []
        
        # Add individual feedback items
        summary_parts.append("## Individual Feedback Items")
        for i, item in enumerate(feedback_items, 1):
            feedback = item.get("feedback")
            chat_info = item.get("chat_info", {})
            
            summary_parts.append(f"\n### Feedback #{i}")
            summary_parts.append(f"**Type**: {feedback.feedback_type.value}")
            summary_parts.append(f"**Date**: {feedback.timestamp.strftime('%Y-%m-%d %H:%M')}")
            summary_parts.append(f"**Summary**: {feedback.summary}")
            summary_parts.append(f"**Raw Message**: {feedback.raw_message}")
            
            if feedback.pain_points:
                summary_parts.append(f"**Pain Points**: {', '.join(feedback.pain_points)}")
            
            if feedback.feature_requests:
                summary_parts.append(f"**Feature Requests**: {', '.join(feedback.feature_requests)}")
            
            if feedback.current_solutions:
                summary_parts.append(f"**Current Solutions**: {', '.join(feedback.current_solutions)}")
            
            if feedback.frequency:
                summary_parts.append(f"**Frequency**: {feedback.frequency}")
            
            if feedback.severity:
                summary_parts.append(f"**Severity**: {feedback.severity}")
            
            # Add conversation context (anonymized)
            if chat_info.get("total_questions"):
                summary_parts.append(f"**Questions Asked**: {chat_info['total_questions']}")
            
            if chat_info.get("conversation_length"):
                summary_parts.append(f"**Conversation Length**: {chat_info['conversation_length']} messages")
        
        # Add cross-chat insights
        if cross_chat_insights:
            summary_parts.append("\n## Cross-Chat Insights")
            for theme, insight in cross_chat_insights.items():
                if insight.frequency_count > 1:  # Only include if mentioned by multiple users
                    summary_parts.append(f"\n### {theme.replace('_', ' ').title()}")
                    summary_parts.append(f"**Type**: {insight.feedback_type.value}")
                    summary_parts.append(f"**Frequency**: Mentioned {insight.frequency_count} times")
                    summary_parts.append(f"**Affected Chats**: {insight.affected_chats} different users")
                    summary_parts.append(f"**Severity**: {insight.severity_level}")
                    summary_parts.append(f"**First Seen**: {insight.first_seen.strftime('%Y-%m-%d')}")
                    summary_parts.append(f"**Last Seen**: {insight.last_seen.strftime('%Y-%m-%d')}")
        
        return "\n".join(summary_parts)
    
    async def triage_feedback_to_linear(self, 
                                      feedback_items: List[Dict[str, Any]], 
                                      cross_chat_insights: Dict[str, CrossChatInsight]) -> List[Dict[str, Any]]:
        """Triage all collected feedback into Linear issues."""
        
        if not feedback_items:
            logger.info("No feedback items to triage")
            return []
        
        # Get team ID
        team_id = await self.linear_client.get_team_id()
        if not team_id:
            logger.error("Could not get Linear team ID")
            return []
        
        # Format feedback using GPT-4o
        formatted_issues = await self.format_feedback_for_linear(feedback_items, cross_chat_insights)
        
        if not formatted_issues:
            logger.error("No issues were formatted by GPT-4o")
            return []
        
        # Create issues in Linear
        created_issues = []
        for issue_data in formatted_issues:
            try:
                title = issue_data.get("title", "Untitled Feedback")
                description = issue_data.get("description", "")
                issue_type = issue_data.get("type", "general_feedback")
                priority_level = issue_data.get("priority", "medium")
                
                # Convert priority level to Linear priority number
                priority_map = {"high": 2, "medium": 3, "low": 4}
                priority = priority_map.get(priority_level, 3)
                
                # Create the issue
                created_issue = await self.linear_client.create_issue(
                    title=title,
                    description=description,
                    team_id=team_id,
                    priority=priority
                )
                
                if created_issue:
                    created_issues.append({
                        "linear_issue": created_issue,
                        "original_data": issue_data,
                        "created_at": datetime.now().isoformat()
                    })
                    logger.info(f"Created Linear issue: {created_issue['identifier']} - {title}")
                
            except Exception as e:
                logger.error(f"Error creating Linear issue: {e}")
                continue
        
        return created_issues
    
    async def triage_chat_session_to_linear(self, 
                                          chat_feedback_data: Dict[str, Any],
                                          session_cross_chat_insights: Optional[Dict[str, CrossChatInsight]] = None) -> List[Dict[str, Any]]:
        """Triage feedback from a specific chat session into Linear issues."""
        
        feedback_items = chat_feedback_data.get("feedback_items", [])
        chat_guid = chat_feedback_data.get("chat_guid", "unknown")
        session_state = chat_feedback_data.get("session_state", "unknown")
        
        if not feedback_items:
            logger.info(f"No feedback items to triage for chat session {chat_guid}")
            return []
        
        logger.info(f"🔄 Starting Linear triaging for chat session {chat_guid}")
        logger.info(f"   Session state: {session_state}")
        logger.info(f"   Feedback items: {len(feedback_items)}")
        logger.info(f"   Questions asked: {chat_feedback_data.get('total_questions_asked', 0)}")
        
        # Get team ID
        team_id = await self.linear_client.get_team_id()
        if not team_id:
            logger.error(f"❌ Could not get Linear team ID for chat session {chat_guid}")
            return []
        
        # Use session-specific cross-chat insights if provided, otherwise empty
        insights = session_cross_chat_insights or {}
        
        # Format feedback using GPT-4o
        logger.info(f"🤖 Formatting feedback with GPT-4o for chat session {chat_guid}")
        formatted_issues = await self.format_feedback_for_linear(feedback_items, insights)
        
        if not formatted_issues:
            logger.error(f"❌ No issues were formatted by GPT-4o for chat session {chat_guid}")
            return []
        
        logger.info(f"✅ GPT-4o formatted {len(formatted_issues)} issues for chat session {chat_guid}")
        
        # Create issues in Linear
        created_issues = []
        for i, issue_data in enumerate(formatted_issues, 1):
            try:
                title = issue_data.get("title", "Untitled Feedback")
                description = issue_data.get("description", "")
                issue_type = issue_data.get("type", "general_feedback")
                priority_level = issue_data.get("priority", "medium")
                
                # Add session context to description
                description += f"\n\n---\n**Session Context:**\n"
                description += f"- Chat Session: {chat_guid[:8]}... (anonymized)\n"
                description += f"- Session State: {session_state}\n"
                description += f"- Total Questions Asked: {chat_feedback_data.get('total_questions_asked', 0)}\n"
                description += f"- Feedback Items: {len(feedback_items)}\n"
                description += f"- Created: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}\n"
                
                # Convert priority level to Linear priority number
                priority_map = {"high": 2, "medium": 3, "low": 4}
                priority = priority_map.get(priority_level, 3)
                
                logger.info(f"🚀 Creating Linear issue {i}/{len(formatted_issues)} for chat session {chat_guid}")
                logger.info(f"   Title: {title}")
                logger.info(f"   Type: {issue_type}")
                logger.info(f"   Priority: {priority_level}")
                
                # Create the issue
                created_issue = await self.linear_client.create_issue(
                    title=title,
                    description=description,
                    team_id=team_id,
                    priority=priority
                )
                
                if created_issue:
                    created_issues.append({
                        "linear_issue": created_issue,
                        "original_data": issue_data,
                        "chat_guid": chat_guid,
                        "session_context": {
                            "state": session_state,
                            "questions_asked": chat_feedback_data.get("total_questions_asked", 0),
                            "feedback_count": len(feedback_items)
                        },
                        "created_at": datetime.now().isoformat()
                    })
                    
                    logger.info(f"✅ Created Linear issue for chat session {chat_guid}:")
                    logger.info(f"   Issue ID: {created_issue['identifier']}")
                    logger.info(f"   Title: {created_issue['title']}")
                    logger.info(f"   URL: {created_issue['url']}")
                    logger.info(f"   Priority: {priority_level}")
                
            except Exception as e:
                logger.error(f"❌ Error creating Linear issue {i} for chat session {chat_guid}: {e}")
                continue
        
        if created_issues:
            logger.info(f"🎉 Successfully created {len(created_issues)} Linear issues for chat session {chat_guid}")
            for issue in created_issues:
                linear_issue = issue["linear_issue"]
                logger.info(f"   ✅ {linear_issue['identifier']}: {linear_issue['title']}")
        else:
            logger.warning(f"⚠️  No Linear issues were created for chat session {chat_guid}")
        
        return created_issues

# Global triager instance
feedback_triager = FeedbackTriager() 