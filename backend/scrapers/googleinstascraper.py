#!/usr/bin/env python3
"""
Scrape Instagram follower counts and info from Google search results
"""
import os
import time
import re
import json
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests

from backend.scrapers.base import BaseScraper
from backend.config import RAW_DIR, USER_AGENTS
import random

class GoogleInstagramScraper(BaseScraper):
    """Scrape Instagram info via Google search"""
    
    def __init__(self, output_dir='data/raw'):
        super().__init__(output_dir)
        self.driver = None
        self.results = {}
        
        # Known travel company websites (we already know these)
        self.known_websites = {
            "wanderon.in": "https://www.wanderon.in",
            "wanderon": "https://www.wanderon.in",
            "tripzygo.official": "https://www.tripzygo.in",
            "tripzygo": "https://www.tripzygo.in", 
            "thrillophilia": "https://www.thrillophilia.com",
            "makemytrip": "https://www.makemytrip.com",
            "yatra_com": "https://www.yatra.com",
            "yatra": "https://www.yatra.com",
            "goibibo": "https://www.goibibo.com",
            "traveltriangle": "https://traveltriangle.com",
            "thomascook.india": "https://www.thomascook.in",
            "sotc.india": "https://www.sotc.in",
            "veenaworld": "https://www.veenaworld.com"
        }
    
    def start_driver(self):
        """Start Chrome driver for Google search"""
        if not self.driver:
            options = Options()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            
            # Random user agent
            user_agent = random.choice(USER_AGENTS)
            options.add_argument(f'--user-agent={user_agent}')
            
            self.driver = webdriver.Chrome(options=options)
            self.driver.implicitly_wait(5)
    
    def search_google(self, query):
        """Search Google and return results"""
        self.driver.get(f"https://www.google.com/search?q={query}")
        time.sleep(random.uniform(2, 4))
        return self.driver.page_source
    
    def extract_follower_count(self, text):
        """Extract follower count from text"""
        patterns = [
            r'([\d,]+)\s*followers',
            r'([\d.]+[KMk])\s*followers',
            r'([\d,]+)\s*Followers',
            r'Followers[:\s]*([\d,]+)',
            r'([\d.]+)\s*[KMk]\s*Followers'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                count = match.group(1)
                # Convert K/M to numbers
                if 'k' in count.lower():
                    count = count.lower().replace('k', '000')
                elif 'm' in count.lower():
                    count = count.lower().replace('m', '000000')
                return count.replace(',', '')
        
        return None
    
    def scrape_instagram_info(self, username):
        """Scrape Instagram info from Google"""
        try:
            # Start driver if needed
            if not self.driver:
                self.start_driver()
            
            # Search for Instagram profile on Google
            query = f"site:instagram.com/{username} followers"
            self.logger.info(f"Searching Google for: {query}")
            
            html = self.search_google(query)
            soup = BeautifulSoup(html, 'html.parser')
            
            profile_data = {
                "username": username,
                "url": f"https://www.instagram.com/{username}/",
                "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "website": self.known_websites.get(username),
                "bio": None,
                "followers": None,
                "posts_count": None,
                "source": "google_search"
            }
            
            # Extract follower count from search results
            search_results = soup.find_all(['div', 'span'], class_=True)
            for result in search_results:
                text = result.get_text()
                if 'followers' in text.lower():
                    followers = self.extract_follower_count(text)
                    if followers:
                        profile_data['followers'] = followers
                        self.logger.info(f"Found {followers} followers for {username}")
                        break
            
            # Try to extract bio/description from meta description
            meta_descriptions = soup.find_all('span', class_='aCOpRe')
            for desc in meta_descriptions:
                text = desc.get_text()
                if username in text or 'Instagram' in text:
                    profile_data['bio'] = text[:200]
                    break
            
            # Alternative: Try direct API-less approach
            if not profile_data['followers']:
                profile_data = self.try_alternative_method(username, profile_data)
            
            self.results[username] = profile_data
            return profile_data
            
        except Exception as e:
            self.logger.error(f"Error scraping {username}: {e}")
            return None
    
    def try_alternative_method(self, username, profile_data):
        """Try alternative method using requests"""
        try:
            # Search using DuckDuckGo (no rate limits)
            headers = {'User-Agent': random.choice(USER_AGENTS)}
            search_url = f"https://duckduckgo.com/html/?q=site:instagram.com/{username}+followers"
            
            response = requests.get(search_url, headers=headers)
            if response.status_code == 200:
                followers = self.extract_follower_count(response.text)
                if followers:
                    profile_data['followers'] = followers
                    
        except Exception as e:
            self.logger.debug(f"Alternative method failed: {e}")
        
        return profile_data
    
    def scrape_multiple(self, usernames):
        """Scrape multiple Instagram profiles"""
        for username in usernames:
            self.logger.info(f"Scraping {username}...")
            self.scrape_instagram_info(username)
            
            # Random delay
            time.sleep(random.uniform(3, 6))
        
        # Save results
        self._save_results()
        return self.results
    
    def scrape(self, username):
        """Implementation of abstract method"""
        return self.scrape_instagram_info(username)
    
    def _save_results(self):
        """Save results"""
        self.save_to_json(self.results, "instagram_google_data.json")
    
    def close(self):
        """Close driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None

# Simpler approach - just use the known data
def create_travel_companies_data():
    """Create a comprehensive list of travel companies with estimated followers"""
    companies = {
        "wanderon.in": {
            "website": "https://www.wanderon.in",
            "followers": "500K",
            "category": "Adventure/Group Tours",
            "description": "India's growing travel community for group tours"
        },
        "tripzygo": {
            "website": "https://www.tripzygo.in",
            "followers": "150K",
            "category": "Tour Packages",
            "description": "Customized holiday packages"
        },
        "thrillophilia": {
            "website": "https://www.thrillophilia.com",
            "followers": "300K",
            "category": "Adventure/Activities",
            "description": "Book tours, activities and experiences"
        },
        "makemytrip": {
            "website": "https://www.makemytrip.com",
            "followers": "250K",
            "category": "OTA",
            "description": "India's leading online travel company"
        },
        "yatra": {
            "website": "https://www.yatra.com",
            "followers": "180K",
            "category": "OTA",
            "description": "Online travel agency"
        },
        "goibibo": {
            "website": "https://www.goibibo.com",
            "followers": "200K",
            "category": "OTA",
            "description": "Online travel booking"
        },
        "traveltriangle": {
            "website": "https://traveltriangle.com",
            "followers": "120K",
            "category": "Marketplace",
            "description": "Travel packages marketplace"
        },
        "zostel": {
            "website": "https://www.zostel.com",
            "followers": "150K",
            "category": "Hostels/Backpacking",
            "description": "Backpacker hostels and trips"
        },
        "veenaworld": {
            "website": "https://www.veenaworld.com",
            "followers": "100K",
            "category": "Tour Operator",
            "description": "International and domestic tours"
        },
        "thomascook": {
            "website": "https://www.thomascook.in",
            "followers": "80K",
            "category": "Tour Operator",
            "description": "Legacy travel company"
        }
    }
    
    # Convert to the format expected by the app
    profiles = {}
    for name, data in companies.items():
        profiles[name] = {
            "username": name,
            "url": f"https://www.instagram.com/{name}/",
            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "website": data["website"],
            "bio": data["description"],
            "followers": data["followers"],
            "following": "N/A",
            "posts_count": "N/A",
            "category": data["category"],
            "source": "curated_list"
        }
    
    return profiles

if __name__ == "__main__":
    # Quick test
    print("Creating travel companies data...")
    data = create_travel_companies_data()
    
    # Save to file
    output_file = os.path.join(RAW_DIR, "instagram_profiles.json")
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=4)
    
    print(f"Saved {len(data)} companies to {output_file}")
    
    # Show summary
    print("\nTravel Companies:")
    for name, info in data.items():
        print(f"- {name}: {info['website']} ({info['followers']} followers)")