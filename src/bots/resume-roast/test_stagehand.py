#!/usr/bin/env python3
"""
Test script for the Stagehand LinkedIn scraper integration.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from stagehand_scraper import stagehand_linkedin_scraper

async def test_linkedin_scraper():
    """Test the Stagehand LinkedIn scraper with a sample profile."""
    
    # Test URL validation
    print("Testing URL validation...")
    
    valid_urls = [
        "https://linkedin.com/in/test-profile",
        "https://www.linkedin.com/in/john-doe",
        "linkedin.com/in/jane-smith"
    ]
    
    invalid_urls = [
        "https://google.com",
        "https://facebook.com/profile",
        "not-a-url"
    ]
    
    print("✅ Valid URLs:")
    for url in valid_urls:
        is_valid = stagehand_linkedin_scraper.is_valid_linkedin_url(url)
        print(f"  {url}: {'✅' if is_valid else '❌'} {is_valid}")
    
    print("\n❌ Invalid URLs:")
    for url in invalid_urls:
        is_valid = stagehand_linkedin_scraper.is_valid_linkedin_url(url)
        print(f"  {url}: {'✅' if is_valid else '❌'} {is_valid}")
    
    # Test URL normalization
    print("\nTesting URL normalization...")
    test_urls = [
        "linkedin.com/in/test",
        "https://linkedin.com/in/test",
        "  https://www.linkedin.com/in/test  "
    ]
    
    for url in test_urls:
        normalized = stagehand_linkedin_scraper.normalize_linkedin_url(url)
        print(f"  '{url}' -> '{normalized}'")
    
    # Test with the problematic URL from the logs
    problematic_url = "http://www.linkedin.com/in/rishabh-jhamnani"
    fixed_url = stagehand_linkedin_scraper.normalize_linkedin_url(problematic_url)
    print(f"  Problem URL fix: '{problematic_url}' -> '{fixed_url}'")
    
    # Test profile scraping (you can uncomment and provide a real LinkedIn URL)
    # WARNING: This will make actual web requests and use API tokens
    """
    print("\nTesting profile scraping...")
    test_profile_url = "https://linkedin.com/in/your-test-profile-here"
    
    try:
        print(f"Scraping profile: {test_profile_url}")
        profile = await stagehand_linkedin_scraper.scrape_profile(test_profile_url)
        
        if profile:
            print("✅ Profile scraped successfully!")
            print(f"  Name: {profile.name}")
            print(f"  Headline: {profile.headline}")
            print(f"  Current Position: {profile.current_position}")
            print(f"  Location: {profile.location}")
            print(f"  Connections: {profile.connections}")
            print(f"  Experience entries: {len(profile.experience)}")
            print(f"  Education entries: {len(profile.education)}")
            print(f"  Skills: {len(profile.skills)}")
            print(f"  Raw text length: {len(profile.raw_text)}")
        else:
            print("❌ Profile scraping failed")
            
    except Exception as e:
        print(f"❌ Error during scraping: {e}")
    """
    
    print("\n🎉 Test completed!")

def check_environment():
    """Check if required environment variables are set."""
    print("Checking environment configuration...")
    
    required_vars = ["OPENAI_API_KEY", "LINKEDIN_EMAIL", "LINKEDIN_PASSWORD"]
    optional_vars = ["BROWSERBASE_API_KEY", "BROWSERBASE_PROJECT_ID"]
    
    missing_required = []
    missing_optional = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)
        else:
            if var == "LINKEDIN_PASSWORD":
                print(f"✅ {var}: {'*' * len(os.getenv(var))}")
            else:
                print(f"✅ {var}: {'*' * 20}...{os.getenv(var)[-4:]}")
    
    for var in optional_vars:
        if not os.getenv(var):
            missing_optional.append(var)
        else:
            print(f"✅ {var}: {'*' * 20}...{os.getenv(var)[-4:]}")
    
    if missing_required:
        print(f"\n❌ Missing required environment variables: {', '.join(missing_required)}")
        print("Please set these in your .env file before running the scraper.")
        return False
    
    if missing_optional:
        print(f"\n⚠️  Missing optional environment variables: {', '.join(missing_optional)}")
        print("The scraper will use local browser mode. For better performance, consider setting these.")
    
    return True

def check_node_installation():
    """Check if Node.js is installed and available."""
    print("\nChecking Node.js installation...")
    
    try:
        import subprocess
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js version: {result.stdout.strip()}")
        else:
            print("❌ Node.js is not working properly")
            return False
            
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ npm version: {result.stdout.strip()}")
        else:
            print("❌ npm is not working properly")
            return False
            
        return True
        
    except FileNotFoundError:
        print("❌ Node.js is not installed or not in PATH")
        print("Please install Node.js from https://nodejs.org/")
        return False

async def main():
    """Main test function."""
    print("🤘 Stagehand LinkedIn Scraper Test")
    print("=" * 50)
    
    # Check prerequisites
    if not check_environment():
        return
    
    if not check_node_installation():
        return
    
    print("\n" + "=" * 50)
    
    # Run tests
    await test_linkedin_scraper()

if __name__ == "__main__":
    asyncio.run(main()) 