import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Project base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Data directories
DATA_DIR = os.path.join(BASE_DIR, 'data')
RAW_DIR = os.path.join(DATA_DIR, 'raw')
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')
CACHE_DIR = os.path.join(DATA_DIR, 'cache')

# Ensure directories exist
for directory in [RAW_DIR, PROCESSED_DIR, CACHE_DIR]:
    os.makedirs(directory, exist_ok=True)

# Instagram handles file
INSTAGRAM_HANDLES_FILE = os.path.join(RAW_DIR, 'instagram_handles.txt')

# Instagram credentials (use environment variables for security)
INSTAGRAM_USERNAME = os.getenv('INSTAGRAM_USERNAME', '')  # Set in .env file
INSTAGRAM_PASSWORD = os.getenv('INSTAGRAM_PASSWORD', '')  # Set in .env file

# Scraping settings
SCRAPER_DELAY_MIN = 2  # Minimum delay between requests in seconds
SCRAPER_DELAY_MAX = 7  # Maximum delay between requests in seconds
USE_SELENIUM_FOR_WEBSITES = True  # Changed to True for better scraping
HEADLESS_BROWSER = False  # Changed to False for Instagram (helps avoid detection)

# Enhanced user agents list
USER_AGENTS = [
    # Chrome on Windows (most common)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    
    # Chrome on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    
    # Safari on Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
    
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
    
    # Mobile user agents
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Mobile Safari/537.36"
]

# Expanded keywords for identifying travel packages
PACKAGE_KEYWORDS = [
    'package', 'packages', 'tour', 'tours', 'trip', 'trips',
    'holiday', 'holidays', 'vacation', 'vacations', 'itinerary',
    'itineraries', 'travel', 'destination', 'destinations',
    'getaway', 'getaways', 'excursion', 'excursions', 'journey',
    'adventure', 'adventures', 'expedition', 'expeditions',
    'experience', 'experiences', 'explore', 'discovery',
    'wanderlust', 'voyage', 'safari', 'trek', 'trekking',
    'backpacking', 'road trip', 'city break', 'weekend trip',
    'group tour', 'private tour', 'custom tour', 'tailor made',
    'honeymoon', 'family tour', 'solo travel', 'budget travel',
    'luxury travel', 'camping', 'glamping', 'workation'
]

# Database settings (if needed later)
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = int(os.getenv('DB_PORT', '5432'))
DB_NAME = os.getenv('DB_NAME', 'trippypick')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')

# Additional settings for better scraping
MAX_RETRIES = 3
TIMEOUT = 30
MAX_PACKAGES_PER_WEBSITE = 20
INSTAGRAM_MAX_PROFILES_PER_SESSION = 50

# Logging settings
LOG_LEVEL = 'INFO'
LOG_FILE = os.path.join(BASE_DIR, 'scraping.log')

# Chrome options for better scraping
CHROME_OPTIONS = [
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--disable-blink-features=AutomationControlled',
    '--disable-infobars',
    '--disable-extensions',
    '--disable-gpu',
    '--disable-dev-tools',
    '--disable-web-security',
    '--disable-features=VizDisplayCompositor',
    '--disable-setuid-sandbox'
]