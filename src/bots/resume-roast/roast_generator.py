import logging
from typing import Optional
from openai import OpenAI
from models import LinkedInProfile
from config import config

logger = logging.getLogger(__name__)

class RoastGenerator:
    """Generates snarky resume roasts using OpenAI GPT-4o."""
    
    def __init__(self):
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.OPENAI_MODEL
    
    def generate_roast(self, profile: LinkedInProfile) -> Optional[str]:
        """
        Generate a snarky but conversational roast based on LinkedIn profile data.
        
        Args:
            profile: LinkedInProfile object with scraped data
            
        Returns:
            Generated roast text or None if generation fails
        """
        try:
            # Prepare the profile data for the prompt
            profile_summary = self._format_profile_for_prompt(profile)
            
            system_prompt = """You are a witty, snarky career roast bot. Your job is to roast people's professional backgrounds in a playful, conversational way. Be cutting but not cruel - think friendly roast, not mean-spirited attack.

Focus on:
- Generic job titles and corporate buzzwords
- Predictable career paths
- Company choices and timing
- Education vs reality gaps
- Professional clichés

Keep it conversational, like you're texting a friend. Use modern slang and casual language. Don't be offensive about protected characteristics. Make it funny, not hurtful.

Length: 2-4 sentences maximum. Make it punchy and memorable."""

            user_prompt = f"""Roast this LinkedIn profile:

{profile_summary}

Be snarky and conversational, like you're texting a friend who asked for honest feedback about their career. Focus on the professional choices, not personal attributes."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=150,
                temperature=0.8,
                presence_penalty=0.3,
                frequency_penalty=0.3
            )
            
            roast = response.choices[0].message.content.strip()
            logger.info(f"Generated roast for profile: {profile.name}")
            return roast
            
        except Exception as e:
            logger.error(f"Error generating roast: {e}")
            return self._get_fallback_roast(profile)
    
    def _format_profile_for_prompt(self, profile: LinkedInProfile) -> str:
        """Format profile data into a readable summary for the AI prompt."""
        summary_parts = []
        
        if profile.name:
            summary_parts.append(f"Name: {profile.name}")
        
        if profile.headline:
            summary_parts.append(f"Headline: {profile.headline}")
        
        if profile.current_position:
            summary_parts.append(f"Current Role: {profile.current_position}")
        
        if profile.experience:
            summary_parts.append("Work Experience:")
            for i, exp in enumerate(profile.experience[:3], 1):  # Limit to top 3
                title = exp.get('title', 'Unknown Role')
                company = exp.get('company', 'Unknown Company')
                summary_parts.append(f"  {i}. {title} at {company}")
        
        if profile.education:
            summary_parts.append("Education:")
            for i, edu in enumerate(profile.education[:2], 1):  # Limit to top 2
                institution = edu.get('institution', 'Unknown School')
                summary_parts.append(f"  {i}. {institution}")
        
        # If we have very little data, include a note
        if len(summary_parts) <= 2:
            summary_parts.append("(Limited profile information available - LinkedIn probably blocked us 😅)")
        
        return "\n".join(summary_parts)
    
    def _get_fallback_roast(self, profile: LinkedInProfile) -> str:
        """Get a generic roast when AI generation fails."""
        fallback_roasts = [
            "Your LinkedIn profile is so private, even the roast bot gave up trying to find something to mock. That's either very strategic or very suspicious... 🤔",
            "LinkedIn locked us out faster than you probably get rejected from job applications. At least we're consistent! 😂",
            "I tried to roast your career but LinkedIn's anti-bot measures are stronger than your professional network apparently... 🤖",
            "Your profile is more protected than your job security. Impressive digital privacy game though! 🔒",
            "LinkedIn said 'nope' to scraping your profile. Even robots have standards these days... 🤷‍♂️"
        ]
        
        import random
        return random.choice(fallback_roasts)
    
    def generate_linkedin_prompt_message(self, message_count: int) -> str:
        """Generate increasingly snarky messages prompting for LinkedIn URL."""
        
        if message_count == 1:
            return "Hey there! 👋 Ready to get your career roasted? Drop your LinkedIn profile URL and let's see what we're working with... 🔥"
        
        elif message_count == 2:
            return "Still waiting for that LinkedIn URL... Are you having second thoughts or just can't figure out how to copy-paste? 😏"
        
        elif message_count == 3:
            return "Ok, this is getting awkward. I need your LinkedIn URL to roast you properly. Don't make me send a passive-aggressive follow-up... 🙄"
        
        elif message_count == 4:
            return "LinkedIn URL. Now. I've got other careers to destroy and you're holding up the line. ⏰"
        
        elif message_count == 5:
            return "Listen, I'm a roast bot, not a therapy bot. Give me your LinkedIn URL or we're done here. 💀"
        
        else:
            return f"Message #{message_count} and still no LinkedIn URL? Your commitment issues are showing... Just paste the damn link already! 😤"
    
    def generate_invalid_url_message(self) -> str:
        """Generate a snarky message for invalid LinkedIn URLs."""
        messages = [
            "That's not a LinkedIn URL, genius. Try again with an actual LinkedIn profile link... 🤦‍♂️",
            "Did you just paste your Tinder profile? I need a LINKEDIN URL. The blue one with the professional headshots... 💼",
            "Nice try, but that's not LinkedIn. I need linkedin.com/in/your-username-here. Basic internet skills, please! 🌐",
            "That URL is about as professional as your career choices. LinkedIn URL only, please... 📎",
            "Wrong link, wrong energy. LinkedIn profile URL or nothing. Don't test my patience... ⚡"
        ]
        
        import random
        return random.choice(messages)

# Global roast generator instance
roast_generator = RoastGenerator() 