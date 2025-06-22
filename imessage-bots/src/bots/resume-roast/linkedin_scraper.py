import re
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
import time
import logging
from models import LinkedInProfile

logger = logging.getLogger(__name__)

class LinkedInScraper:
    """Scrapes LinkedIn profiles for resume roasting."""
    
    def __init__(self):
        self.session = requests.Session()
        # Set realistic headers to avoid bot detection
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def is_valid_linkedin_url(self, url: str) -> bool:
        """Check if the provided URL is a valid LinkedIn profile URL."""
        try:
            parsed = urlparse(url.strip())
            # Check for common LinkedIn profile URL patterns
            linkedin_patterns = [
                r'linkedin\.com/in/[\w-]+/?$',
                r'linkedin\.com/pub/[\w-]+/\d+/\d+/\d+/?$',
                r'www\.linkedin\.com/in/[\w-]+/?$',
                r'www\.linkedin\.com/pub/[\w-]+/\d+/\d+/\d+/?$'
            ]
            
            full_url = f"{parsed.netloc}{parsed.path}"
            return any(re.search(pattern, full_url) for pattern in linkedin_patterns)
        except Exception:
            return False
    
    def normalize_linkedin_url(self, url: str) -> str:
        """Normalize LinkedIn URL to ensure it's properly formatted."""
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        return url
    
    def scrape_profile(self, url: str) -> Optional[LinkedInProfile]:
        """
        Scrape a LinkedIn profile and extract relevant information.
        
        Note: LinkedIn has strong anti-scraping measures. This is a basic implementation
        that may not work consistently. For production use, consider LinkedIn's official API.
        """
        try:
            if not self.is_valid_linkedin_url(url):
                logger.warning(f"Invalid LinkedIn URL: {url}")
                return None
            
            normalized_url = self.normalize_linkedin_url(url)
            logger.info(f"Scraping LinkedIn profile: {normalized_url}")
            
            # Add delay to be respectful
            time.sleep(2)
            
            response = self.session.get(normalized_url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract basic information
            profile = LinkedInProfile()
            profile.raw_text = response.text
            
            # Try to extract name from various possible selectors
            name_selectors = [
                'h1[class*="text-heading"]',
                '.pv-text-details__left-panel h1',
                '.top-card-layout__title',
                'h1.top-card-layout__title'
            ]
            
            for selector in name_selectors:
                name_element = soup.select_one(selector)
                if name_element:
                    profile.name = name_element.get_text(strip=True)
                    break
            
            # Try to extract headline
            headline_selectors = [
                '.pv-text-details__left-panel .text-body-medium',
                '.top-card-layout__headline',
                '[class*="headline"]'
            ]
            
            for selector in headline_selectors:
                headline_element = soup.select_one(selector)
                if headline_element:
                    profile.headline = headline_element.get_text(strip=True)
                    break
            
            # Extract experience information from the page text
            # This is a fallback method since LinkedIn's dynamic content is hard to scrape
            profile.experience = self._extract_experience_from_text(response.text)
            
            # Extract education if available
            profile.education = self._extract_education_from_text(response.text)
            
            logger.info(f"Successfully scraped profile for: {profile.name}")
            return profile
            
        except requests.RequestException as e:
            logger.error(f"Network error scraping LinkedIn profile: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error scraping LinkedIn profile: {e}")
            return None
    
    def _extract_experience_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract work experience from page text using regex patterns."""
        experience = []
        
        # Look for common job title patterns
        job_patterns = [
            r'(Software Engineer|Data Scientist|Product Manager|Marketing Manager|Sales Manager|Director|VP|CEO|CTO|CFO|Manager|Analyst|Consultant|Developer|Designer|Coordinator|Specialist|Associate|Senior|Junior|Lead|Principal|Staff)',
            r'(Engineer|Scientist|Manager|Director|Analyst|Consultant|Developer|Designer|Coordinator|Specialist|Associate)'
        ]
        
        company_patterns = [
            r'at\s+([A-Z][a-zA-Z\s&.,]+?)(?:\s+·|\s+\||$)',
            r'@\s*([A-Z][a-zA-Z\s&.,]+?)(?:\s+·|\s+\||$)'
        ]
        
        for pattern in job_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                job_title = match.group(0)
                # Look for company name near the job title
                surrounding_text = text[max(0, match.start()-100):match.end()+100]
                
                for comp_pattern in company_patterns:
                    company_match = re.search(comp_pattern, surrounding_text)
                    if company_match:
                        company = company_match.group(1).strip()
                        experience.append({
                            'title': job_title,
                            'company': company,
                        })
                        break
        
        # Remove duplicates
        seen = set()
        unique_experience = []
        for exp in experience:
            key = (exp.get('title', ''), exp.get('company', ''))
            if key not in seen:
                seen.add(key)
                unique_experience.append(exp)
        
        return unique_experience[:5]  # Limit to 5 most relevant experiences
    
    def _extract_education_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract education information from page text."""
        education = []
        
        # Look for university/college patterns
        edu_patterns = [
            r'(University|College|School|Institute|Academy)\s+of\s+[\w\s]+',
            r'[\w\s]+\s+(University|College|School|Institute|Academy)',
            r'(Bachelor|Master|PhD|MBA|BS|MS|MA|BA)\s+(?:of\s+|in\s+)?[\w\s]+',
        ]
        
        for pattern in edu_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                education.append({
                    'institution': match.group(0).strip()
                })
        
        # Remove duplicates and limit
        seen = set()
        unique_education = []
        for edu in education:
            key = edu.get('institution', '')
            if key not in seen and len(key) > 5:  # Filter out very short matches
                seen.add(key)
                unique_education.append(edu)
        
        return unique_education[:3]  # Limit to 3 most relevant

# Global scraper instance
linkedin_scraper = LinkedInScraper() 