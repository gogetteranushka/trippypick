import time
import random
import json
import os
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class BaseScraper(ABC):
    """Base class for all scrapers with common functionality"""
    
    def __init__(self, output_dir='data/raw'):
        """
        Initialize the base scraper
        
        Args:
            output_dir (str): Directory to save scraped data
        """
        self.output_dir = output_dir
        self.session = self._create_session()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
    
    def _create_session(self):
        """Create a requests session with retry capability"""
        session = requests.Session()
        
        # Set up retry strategy
        retries = Retry(
            total=5,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        
        # Add adapter with retry strategy to session
        adapter = HTTPAdapter(max_retries=retries)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set a user agent from the list
        from backend.config import USER_AGENTS
        user_agent = random.choice(USER_AGENTS)
        session.headers.update({
            "User-Agent": user_agent,
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        })
        
        return session
    
    def _rotate_user_agent(self):
        """Rotate user agent to avoid detection"""
        if self.session is None:
            return None
            
        from backend.config import USER_AGENTS
        user_agent = random.choice(USER_AGENTS)
        self.session.headers.update({
            "User-Agent": user_agent
        })
        return user_agent
    
    def random_delay(self, min_seconds=None, max_seconds=None):
        """Add a random delay between requests"""
        from backend.config import SCRAPER_DELAY_MIN, SCRAPER_DELAY_MAX
        
        min_seconds = min_seconds or SCRAPER_DELAY_MIN
        max_seconds = max_seconds or SCRAPER_DELAY_MAX
        
        delay = random.uniform(min_seconds, max_seconds)
        self.logger.debug(f"Waiting {delay:.2f} seconds...")
        time.sleep(delay)
        return delay
    
    def fetch_url(self, url, timeout=30):
        """
        Fetch content from a URL with error handling
        
        Args:
            url (str): URL to fetch
            timeout (int): Request timeout in seconds
            
        Returns:
            str: HTML content if successful, None otherwise
        """
        try:
            # Rotate user agent occasionally
            if random.random() < 0.3:  # 30% chance to rotate
                self._rotate_user_agent()
                
            self.logger.info(f"Fetching URL: {url}")
            response = self.session.get(url, timeout=timeout)
            
            if response.status_code == 200:
                return response.text
            else:
                self.logger.warning(f"Failed to fetch URL {url}: Status code {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching URL {url}: {e}")
            return None
    
    def save_to_json(self, data, filename):
        """Save data to a JSON file"""
        filepath = os.path.join(self.output_dir, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            self.logger.info(f"Data saved to {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving data to {filepath}: {e}")
            return False
    
    def _save_results(self):
        """Save results to a JSON file - to be implemented by subclasses"""
        pass
    
    @abstractmethod
    def scrape(self, target):
        """
        Abstract method for scraping a target
        
        Args:
            target: The target to scrape (URL, username, etc.)
            
        Returns:
            dict: Extracted data
        """
        pass