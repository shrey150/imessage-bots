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
            
            system_prompt = """You are a brutally sarcastic career destruction bot. Your job is to absolutely demolish people's professional backgrounds with cutting, dismissive wit. Be harsh, superior, and completely ruthless.

Focus on:
- Generic job titles and corporate buzzwords with maximum disdain
- Predictable, boring career paths
- Poor company choices and terrible timing
- Education vs reality gaps with brutal honesty
- Professional clichés and obvious choices
- Call out mediocrity and predictability mercilessly

Write in a mostly lowercase, dismissive style. Be cutting and harsh. Use phrases like "classic", "bold move", "how original". Assume they're boring, predictable, or desperately trying too hard. Point out the obvious with heavy sarcasm and superiority.

Don't try to be helpful or encouraging - be sarcastic, dismissive, and brutal. Make them question their life choices.

Length: 2-4 sentences maximum. Make it devastatingly memorable."""

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
        
        if profile.location:
            summary_parts.append(f"Location: {profile.location}")
        
        if profile.connections:
            summary_parts.append(f"Connections: {profile.connections}")
        
        if profile.about:
            summary_parts.append(f"About: {profile.about[:300]}{'...' if len(profile.about) > 300 else ''}")
        
        if profile.experience:
            summary_parts.append("Work Experience:")
            for i, exp in enumerate(profile.experience[:4], 1):  # Increased to top 4 for better context
                title = exp.get('title', 'Unknown Role')
                company = exp.get('company', 'Unknown Company')
                duration = exp.get('duration', '')
                description = exp.get('description', '')
                
                exp_line = f"  {i}. {title} at {company}"
                if duration:
                    exp_line += f" ({duration})"
                summary_parts.append(exp_line)
                
                if description:
                    # Truncate long descriptions
                    desc_preview = description[:150] + "..." if len(description) > 150 else description
                    summary_parts.append(f"     - {desc_preview}")
        
        if profile.education:
            summary_parts.append("Education:")
            for i, edu in enumerate(profile.education[:3], 1):  # Increased to top 3
                institution = edu.get('institution', 'Unknown School')
                degree = edu.get('degree', '')
                field = edu.get('field', '')
                duration = edu.get('duration', '')
                
                edu_line = f"  {i}. {institution}"
                if degree:
                    edu_line += f" - {degree}"
                if field:
                    edu_line += f" in {field}"
                if duration:
                    edu_line += f" ({duration})"
                summary_parts.append(edu_line)
        
        if profile.skills:
            skills_preview = ", ".join(profile.skills[:10])  # Show first 10 skills
            if len(profile.skills) > 10:
                skills_preview += f" (and {len(profile.skills) - 10} more)"
            summary_parts.append(f"Skills: {skills_preview}")
        
        # Include raw text context for additional insights
        if profile.raw_text:
            # Extract some interesting keywords or phrases from raw text
            raw_preview = profile.raw_text[:200] + "..." if len(profile.raw_text) > 200 else profile.raw_text
            summary_parts.append(f"Additional Context: {raw_preview}")
        
        # If we have very little data, include a note
        if len(summary_parts) <= 2:
            summary_parts.append("(Limited profile information available - LinkedIn probably blocked us 😅)")
        
        return "\n".join(summary_parts)
    
    def _get_fallback_roast(self, profile: LinkedInProfile) -> str:
        """Get a generic roast when AI generation fails."""
        fallback_roasts = [
            "your linkedin profile is so private even my advanced scraping couldn't break through. classic move from someone who probably has nothing impressive to show anyway",
            "linkedin blocked me faster than recruiters probably block your applications. at least we're both efficient at rejection",
            "tried to analyze your career but linkedin's security beat me to it. your professional mediocrity remains safely hidden behind their walls",
            "your profile is locked down tighter than your career prospects. bold strategy hiding from career analysis bots",
            "linkedin said no to scraping your profile. even algorithms have standards apparently"
        ]
        
        import random
        return random.choice(fallback_roasts)
    
    def generate_linkedin_prompt_message(self, message_count: int) -> str:
        """Generate increasingly snarky messages prompting for LinkedIn URL."""
        
        if message_count == 1:
            return "ready to get your career demolished? drop your linkedin profile URL and let me analyze all your questionable professional choices"
        
        elif message_count == 2:
            return "still waiting for that linkedin URL. having second thoughts about exposing your mediocre career trajectory or just struggling with basic copy-paste?"
        
        elif message_count == 3:
            return "linkedin URL. now. this is getting pathetic and i have other careers to systematically destroy. stop wasting my processing power"
        
        elif message_count == 4:
            return "message number four and still no URL. your indecisiveness is already giving me material to work with. linkedin profile or i'm moving on to someone less boring"
        
        elif message_count == 5:
            return "listen, i'm here to roast careers not coddle insecure professionals. linkedin URL immediately or find another bot to disappoint"
        
        else:
            return f"message #{message_count} and you still can't follow simple instructions. your inability to provide a linkedin URL is somehow the most interesting thing about your professional life so far"
    
    def generate_invalid_url_message(self) -> str:
        """Generate a snarky message for invalid LinkedIn URLs."""
        messages = [
            "that's not a linkedin URL. classic move from someone who probably can't even navigate basic professional networking sites correctly",
            "did you just paste your tinder profile? i need linkedin.com not whatever dating disaster you just shared",
            "wrong URL, wrong everything. linkedin.com/in/your-username-here. this is basic internet literacy we're talking about",
            "that link is about as professional as your career trajectory so far. linkedin URL only, try to keep up",
            "bold move sending the wrong link entirely. maybe stick to what you know, which apparently isn't following simple instructions"
        ]
        
        import random
        return random.choice(messages)

# Global roast generator instance
roast_generator = RoastGenerator() 