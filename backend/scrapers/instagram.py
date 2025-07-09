import time
import json
import os
import random
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
import undetected_chromedriver as uc

from backend.scrapers.base import BaseScraper
from backend.config import HEADLESS_BROWSER, USER_AGENTS

class InstagramScraper(BaseScraper):
    """Improved Instagram scraper with better anti-detection"""
    
    def __init__(self, output_dir='data/raw', headless=None):
        super().__init__(output_dir)
        self.headless = HEADLESS_BROWSER if headless is None else headless
        self.driver = None
        self.logged_in = False
        self.results = {}
    
    def start_driver(self):
        """Start undetected Chrome driver"""
        if self.driver is None:
            self.logger.info("Starting undetected Chrome WebDriver")
            
            # Use undetected-chromedriver to bypass detection
            options = uc.ChromeOptions()
            
            # Minimal options to avoid detection
            options.add_argument('--disable-blink-features=AutomationControlled')
            
            if self.headless:
                options.add_argument('--headless=new')
            
            # Create driver
            self.driver = uc.Chrome(options=options)
            
            # Set realistic window size
            self.driver.set_window_size(1366, 768)
            
    def human_type(self, element, text):
        """Type like a human with random delays"""
        element.clear()
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))
    
    def random_mouse_movement(self):
        """Simulate random mouse movements"""
        try:
            # Move to random element
            elements = self.driver.find_elements(By.TAG_NAME, "div")
            if elements:
                random_element = random.choice(elements[:10])
                self.driver.execute_script("arguments[0].scrollIntoView();", random_element)
                time.sleep(random.uniform(0.5, 1.5))
        except:
            pass
    
    def login(self, username, password):
        """Improved login with better anti-detection"""
        if self.logged_in:
            return True
            
        try:
            self.start_driver()
            
            # First, visit Instagram homepage
            self.logger.info("Navigating to Instagram...")
            self.driver.get("https://www.instagram.com")
            time.sleep(random.uniform(3, 5))
            
            # Handle cookie consent
            try:
                cookie_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Allow') or contains(text(), 'Accept')]")
                cookie_button.click()
                time.sleep(random.uniform(1, 2))
            except:
                pass
            
            # Random mouse movement
            self.random_mouse_movement()
            
            # Find and fill username
            self.logger.info("Entering credentials...")
            try:
                username_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.NAME, "username"))
                )
                self.human_type(username_input, username)
                
                # Tab to password field
                time.sleep(random.uniform(0.5, 1))
                password_input = self.driver.find_element(By.NAME, "password")
                self.human_type(password_input, password)
                
                # Wait before clicking login
                time.sleep(random.uniform(1, 2))
                
                # Find and click login button
                login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']//div[text()='Log in']")
                login_button.click()
                
                # Wait for login to complete
                time.sleep(random.uniform(5, 8))
                
                # Check if logged in
                if "accounts/onetap" in self.driver.current_url or len(self.driver.find_elements(By.XPATH, "//img[contains(@alt, 'profile picture')]")) > 0:
                    self.logged_in = True
                    self.logger.info("Successfully logged in!")
                    
                    # Handle "Save Login Info" popup
                    try:
                        not_now = self.driver.find_element(By.XPATH, "//button[text()='Not Now']")
                        not_now.click()
                        time.sleep(random.uniform(1, 2))
                    except:
                        pass
                    
                    # Handle notifications popup
                    try:
                        not_now = self.driver.find_element(By.XPATH, "//button[text()='Not Now']")
                        not_now.click()
                    except:
                        pass
                    
                    return True
                else:
                    self.logger.error("Login failed - could not verify success")
                    return False
                    
            except Exception as e:
                self.logger.error(f"Login error: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during login: {e}")
            return False
    
    def scrape_profile(self, username):
        """Scrape profile with better website extraction"""
        try:
            if not self.logged_in:
                self.logger.warning("Not logged in. Attempting to scrape without login...")
            
            # Ensure driver is started
            if not self.driver:
                self.start_driver()
            
            profile_url = f"https://www.instagram.com/{username}/"
            self.logger.info(f"Scraping profile: {username}")
            
            self.driver.get(profile_url)
            time.sleep(random.uniform(3, 5))
            
            # Check if profile exists
            if "Sorry, this page isn't available" in self.driver.page_source:
                self.logger.warning(f"Profile {username} not found")
                return None
            
            # Initialize profile data
            profile_data = {
                "username": username,
                "url": profile_url,
                "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "website": None,
                "bio": None,
                "followers": None,
                "following": None,
                "posts_count": None
            }
            
            # Wait for profile to load
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//header"))
                )
            except:
                self.logger.warning(f"Profile {username} took too long to load")
            
            # Extract website - multiple strategies
            website_found = False
            
            # Strategy 1: Look for external link button
            try:
                external_link = self.driver.find_element(By.XPATH, "//a[contains(@href, 'l.instagram.com/')]")
                website_url = external_link.get_attribute('href')
                if website_url:
                    # Extract actual URL from Instagram redirect
                    if '?u=' in website_url:
                        import urllib.parse
                        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(website_url).query)
                        if 'u' in parsed:
                            profile_data["website"] = urllib.parse.unquote(parsed['u'][0])
                            website_found = True
                            self.logger.info(f"Found website via external link: {profile_data['website']}")
            except:
                pass
            
            # Strategy 2: Look in bio text for URLs
            if not website_found:
                try:
                    bio_section = self.driver.find_element(By.XPATH, "//section//div[contains(@style, 'line-height')]")
                    bio_text = bio_section.text
                    profile_data["bio"] = bio_text
                    
                    # Extract URL from bio
                    import re
                    url_pattern = r'(?:www\.|https?://)\S+'
                    urls = re.findall(url_pattern, bio_text)
                    if urls:
                        profile_data["website"] = urls[0]
                        if not profile_data["website"].startswith('http'):
                            profile_data["website"] = 'https://' + profile_data["website"]
                        website_found = True
                        self.logger.info(f"Found website in bio: {profile_data['website']}")
                except:
                    pass
            
            # Strategy 3: Check page source for any external links
            if not website_found:
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                for link in soup.find_all('a', href=True):
                    href = link.get('href')
                    if href and 'instagram.com' not in href and href.startswith('http'):
                        profile_data["website"] = href
                        website_found = True
                        self.logger.info(f"Found website in page source: {href}")
                        break
            
            # Extract other profile data
            try:
                # Followers
                followers_elem = self.driver.find_element(By.XPATH, "//a[contains(@href, '/followers/')]/span/span")
                profile_data["followers"] = followers_elem.text
            except:
                self.logger.debug(f"Could not extract followers for {username}")
            
            # Store and save results
            self.results[username] = profile_data
            self._save_results()
            
            return profile_data
            
        except Exception as e:
            self.logger.error(f"Error scraping profile {username}: {e}")
            return None
    
    def scrape_profiles(self, usernames):
        """Scrape multiple profiles with delays"""
        for i, username in enumerate(usernames):
            self.logger.info(f"Scraping profile {i+1}/{len(usernames)}: {username}")
            self.scrape_profile(username)
            
            # Random delay between profiles
            if i < len(usernames) - 1:
                delay = random.uniform(5, 10)
                self.logger.info(f"Waiting {delay:.1f} seconds before next profile...")
                time.sleep(delay)
        
        return self.results
    
    def _save_results(self):
        """Save results to JSON"""
        self.save_to_json(self.results, "instagram_profiles.json")
    
    def scrape(self, username):
        """
        Implementation of abstract scrape method from BaseScraper
        
        Args:
            username (str): Instagram username to scrape
            
        Returns:
            dict: Extracted profile data
        """
        return self.scrape_profile(username)
    
    def close(self):
        """Close the driver"""
        if self.driver:
            self.logger.info("Closing Chrome WebDriver")
            self.driver.quit()
            self.driver = None
            self.logged_in = False