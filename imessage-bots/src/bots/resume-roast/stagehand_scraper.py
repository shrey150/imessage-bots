import asyncio
import json
import logging
import subprocess
import tempfile
import os
from typing import Optional, Dict, Any
from urllib.parse import urlparse
from models import LinkedInProfile

logger = logging.getLogger(__name__)

class StagehandLinkedInScraper:
    """Scrapes LinkedIn profiles using Stagehand for resume roasting."""
    
    def __init__(self):
        self.node_script_template = """
const { Stagehand } = require("@browserbasehq/stagehand");
const { z } = require("zod");

async function scrapeLinkedInProfile(url, email, password) {
    const stagehand = new Stagehand({
        env: "LOCAL",
        verbose: 1,
        debugDom: true,
        enableCaching: true,
        browserbaseAPIKey: process.env.BROWSERBASE_API_KEY,
        openAIAPIKey: process.env.OPENAI_API_KEY,
    });

    try {
        await stagehand.init();
        const page = stagehand.page;
        
        console.log("Step 1: Logging into LinkedIn...");
        
        // Navigate to LinkedIn login page
        await page.goto("https://www.linkedin.com/login", { waitUntil: 'networkidle' });
        await page.waitForTimeout(2000);
        
        // Fill in email
        await page.act(`Type "${email}" into the email field`);
        await page.waitForTimeout(1000);
        
        // Fill in password
        await page.act(`Type "${password}" into the password field`);
        await page.waitForTimeout(1000);
        
        // Click sign in button
        await page.act("Click the Sign in button");
        await page.waitForTimeout(5000);
        
        // Check if login was successful
        const currentUrl = page.url();
        if (currentUrl.includes('challenge') || currentUrl.includes('verify') || currentUrl.includes('checkpoint')) {
            console.log("LinkedIn verification challenge detected. Waiting for manual intervention...");
            // Wait longer for manual verification if needed
            await page.waitForTimeout(30000);
        } else if (currentUrl.includes('login')) {
            // Still on login page - login might have failed
            console.log("Login may have failed. Still on login page.");
            const errorMessage = await page.extract({
                instruction: "Look for any error messages on the login page",
                schema: z.object({
                    error: z.string().optional().describe("Any error message displayed")
                })
            });
            if (errorMessage.error) {
                throw new Error(`LinkedIn login failed: ${errorMessage.error}`);
            } else {
                throw new Error("LinkedIn login failed: Invalid credentials or other issue");
            }
        } else if (currentUrl.includes('feed') || currentUrl.includes('mynetwork') || currentUrl.includes('linkedin.com')) {
            console.log("Login successful!");
        }
        
        console.log("Step 2: Navigating to profile...");
        console.log(`Attempting to navigate to: ${url}`);
        
        // Navigate to LinkedIn profile with increased timeout
        try {
            await page.goto(url, { 
                waitUntil: 'networkidle',
                timeout: 60000  // Increased timeout to 60 seconds
            });
        } catch (error) {
            if (error.message.includes('Timeout')) {
                console.log("Navigation timeout - trying with domcontentloaded instead...");
                try {
                    await page.goto(url, { 
                        waitUntil: 'domcontentloaded',
                        timeout: 45000 
                    });
                } catch (secondError) {
                    console.log("Second navigation attempt failed, trying with load event...");
                    await page.goto(url, { 
                        waitUntil: 'load',
                        timeout: 30000 
                    });
                }
            } else {
                throw error;
            }
        }
        
        // Wait for the page to fully load
        await page.waitForTimeout(8000);
        
        // Check if we actually reached the profile page
        const finalUrl = page.url();
        console.log(`Final URL: ${finalUrl}`);
        
        if (finalUrl.includes('linkedin.com/in/') || finalUrl.includes('linkedin.com/pub/')) {
            console.log("Successfully reached LinkedIn profile page");
        } else if (finalUrl.includes('authwall') || finalUrl.includes('login')) {
            throw new Error("Redirected to authentication wall - profile may be private or login session expired");
        } else {
            console.log("Warning: May not be on expected profile page, but continuing...");
        }
        
        console.log("Step 3: Extracting profile data...");
        
        // First, try to scroll down to load more content
        await page.evaluate(() => {
            window.scrollTo(0, document.body.scrollHeight / 2);
        });
        await page.waitForTimeout(2000);
        
        await page.evaluate(() => {
            window.scrollTo(0, document.body.scrollHeight);
        });
        await page.waitForTimeout(3000);
        
        // Extract profile information using Stagehand's extract method
        const profileData = await page.extract({
            instruction: "Extract comprehensive LinkedIn profile information including name, headline, current position, work experience, education, skills, and any other professional details visible on the profile page. If some information is not available, that's okay - extract what you can see.",
            schema: z.object({
                name: z.string().describe("The person's full name"),
                headline: z.string().optional().describe("Their professional headline or tagline"),
                currentPosition: z.string().optional().describe("Their current job title and company"),
                location: z.string().optional().describe("Their location"),
                about: z.string().optional().describe("Their about/summary section"),
                experience: z.array(z.object({
                    title: z.string().describe("Job title"),
                    company: z.string().describe("Company name"),
                    duration: z.string().optional().describe("How long they worked there"),
                    description: z.string().optional().describe("Job description or responsibilities")
                })).optional().describe("Work experience entries"),
                education: z.array(z.object({
                    institution: z.string().describe("School or university name"),
                    degree: z.string().optional().describe("Degree or program"),
                    field: z.string().optional().describe("Field of study"),
                    duration: z.string().optional().describe("Duration of study")
                })).optional().describe("Education entries"),
                skills: z.array(z.string()).optional().describe("Listed skills"),
                connections: z.string().optional().describe("Number of connections"),
                profileUrl: z.string().optional().describe("LinkedIn profile URL"),
                rawText: z.string().describe("All visible text content from the profile for additional context")
            })
        });
        
        console.log("Profile data extraction completed");

        console.log(JSON.stringify({
            success: true,
            data: profileData
        }));

    } catch (error) {
        console.log(JSON.stringify({
            success: false,
            error: error.message
        }));
    } finally {
        await stagehand.close();
    }
}

// Get arguments from command line
const url = process.argv[2];
const email = process.argv[3];
const password = process.argv[4];

if (!url) {
    console.log(JSON.stringify({
        success: false,
        error: "No URL provided"
    }));
    process.exit(1);
}

if (!email || !password) {
    console.log(JSON.stringify({
        success: false,
        error: "LinkedIn email and password are required"
    }));
    process.exit(1);
}

scrapeLinkedInProfile(url, email, password);
"""
    
    def is_valid_linkedin_url(self, url: str) -> bool:
        """Check if the provided URL is a valid LinkedIn profile URL."""
        try:
            parsed = urlparse(url.strip())
            # More comprehensive LinkedIn URL patterns
            return (
                'linkedin.com' in parsed.netloc.lower() and
                ('/in/' in parsed.path or '/pub/' in parsed.path)
            )
        except Exception:
            return False
    
    def normalize_linkedin_url(self, url: str) -> str:
        """Normalize LinkedIn URL to ensure it's properly formatted."""
        url = url.strip()
        
        # Ensure HTTPS protocol
        if url.startswith('http://'):
            url = url.replace('http://', 'https://')
        elif not url.startswith('https://'):
            url = 'https://' + url
        
        # Ensure www subdomain for better compatibility
        if url.startswith('https://linkedin.com'):
            url = url.replace('https://linkedin.com', 'https://www.linkedin.com')
            
        return url
    
    async def scrape_profile(self, url: str) -> Optional[LinkedInProfile]:
        """
        Scrape a LinkedIn profile using Stagehand and extract relevant information.
        
        Args:
            url: LinkedIn profile URL
            
        Returns:
            LinkedInProfile object with scraped data or None if scraping fails
        """
        try:
            if not self.is_valid_linkedin_url(url):
                logger.warning(f"Invalid LinkedIn URL: {url}")
                return None

            normalized_url = self.normalize_linkedin_url(url)
            logger.info(f"Scraping LinkedIn profile with Stagehand: {normalized_url}")

            # Create temporary directory for Node.js script
            with tempfile.TemporaryDirectory() as temp_dir:
                # Write the Node.js script
                script_path = os.path.join(temp_dir, 'scrape_linkedin.js')
                with open(script_path, 'w') as f:
                    f.write(self.node_script_template)
                
                # Create package.json
                package_json = {
                    "name": "linkedin-scraper",
                    "version": "1.0.0",
                    "type": "commonjs",
                    "dependencies": {
                        "@browserbasehq/stagehand": "^2.3.1",
                        "zod": "^3.22.0"
                    }
                }
                
                package_path = os.path.join(temp_dir, 'package.json')
                with open(package_path, 'w') as f:
                    json.dump(package_json, f, indent=2)
                
                # Install dependencies
                logger.info("Installing Stagehand dependencies...")
                install_process = await asyncio.create_subprocess_exec(
                    'npm', 'install',
                    cwd=temp_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                install_stdout, install_stderr = await install_process.communicate()
                
                if install_process.returncode != 0:
                    logger.error(f"Failed to install dependencies: {install_stderr.decode()}")
                    return None
                
                # Set up environment variables
                env = os.environ.copy()
                # These should be set in your .env file
                env['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', '')
                env['BROWSERBASE_API_KEY'] = os.getenv('BROWSERBASE_API_KEY', '')
                
                # Get LinkedIn credentials
                linkedin_email = os.getenv('LINKEDIN_EMAIL', '')
                linkedin_password = os.getenv('LINKEDIN_PASSWORD', '')
                
                if not linkedin_email or not linkedin_password:
                    logger.error("LinkedIn credentials are required. Please set LINKEDIN_EMAIL and LINKEDIN_PASSWORD in your .env file.")
                    return None
                
                # Run the scraping script with LinkedIn credentials
                logger.info("Running Stagehand scraper with LinkedIn authentication...")
                process = await asyncio.create_subprocess_exec(
                    'node', script_path, normalized_url, linkedin_email, linkedin_password,
                    cwd=temp_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=env
                )
                
                stdout, stderr = await process.communicate()
                
                # Log the raw output for debugging
                stdout_text = stdout.decode().strip()
                stderr_text = stderr.decode().strip()
                
                logger.info(f"Node.js stdout: {stdout_text}")
                if stderr_text:
                    logger.info(f"Node.js stderr: {stderr_text}")
                
                if process.returncode != 0:
                    logger.error(f"Stagehand process failed with return code {process.returncode}")
                    logger.error(f"stderr: {stderr_text}")
                    return None
                
                # Parse the JSON result - find the last JSON object in stdout
                try:
                    # Split by newlines and find the last line that looks like JSON
                    lines = stdout_text.split('\n')
                    json_result = None
                    
                    for line in reversed(lines):
                        line = line.strip()
                        if line.startswith('{') and line.endswith('}'):
                            try:
                                json_result = json.loads(line)
                                break
                            except json.JSONDecodeError:
                                continue
                    
                    if not json_result:
                        logger.error("No valid JSON found in output")
                        logger.error(f"Raw output: {stdout_text}")
                        return None
                    
                    result = json_result
                    
                    if not result.get('success'):
                        logger.error(f"Scraping failed: {result.get('error')}")
                        return None
                    
                    data = result['data']
                    
                    # Create LinkedInProfile object
                    profile = LinkedInProfile()
                    profile.name = data.get('name', '')
                    profile.headline = data.get('headline', '')
                    profile.current_position = data.get('currentPosition', '')
                    profile.location = data.get('location', '')
                    profile.about = data.get('about', '')
                    profile.raw_text = data.get('rawText', '')
                    profile.profile_url = normalized_url
                    
                    # Convert experience data
                    if data.get('experience'):
                        profile.experience = [
                            {
                                'title': exp.get('title', ''),
                                'company': exp.get('company', ''),
                                'duration': exp.get('duration', ''),
                                'description': exp.get('description', '')
                            }
                            for exp in data['experience']
                        ]
                    
                    # Convert education data
                    if data.get('education'):
                        profile.education = [
                            {
                                'institution': edu.get('institution', ''),
                                'degree': edu.get('degree', ''),
                                'field': edu.get('field', ''),
                                'duration': edu.get('duration', '')
                            }
                            for edu in data['education']
                        ]
                    
                    # Set skills
                    profile.skills = data.get('skills', [])
                    profile.connections = data.get('connections', '')
                    
                    logger.info(f"Successfully scraped profile for: {profile.name}")
                    logger.info(f"Profile data summary: {len(profile.experience)} experience entries, {len(profile.education)} education entries, {len(profile.skills)} skills")
                    return profile
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON result: {e}")
                    logger.error(f"Raw output: {stdout_text}")
                    return None
                except Exception as e:
                    logger.error(f"Unexpected error parsing result: {e}")
                    logger.error(f"Raw output: {stdout_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Unexpected error scraping LinkedIn profile: {e}")
            return None

# Global scraper instance
stagehand_linkedin_scraper = StagehandLinkedInScraper() 