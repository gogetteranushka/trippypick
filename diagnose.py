#!/usr/bin/env python3
"""
Diagnostic tool for TrippyPick scraper
Helps identify and fix common issues
"""

import os
import sys
import json
import platform
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is suitable"""
    version = sys.version_info
    print(f"Python Version: {version.major}.{version.minor}.{version.micro}")
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        return False, "Python 3.7+ required"
    return True, "✓ Python version OK"

def check_dependencies():
    """Check if all required packages are installed"""
    required = [
        'beautifulsoup4', 'requests', 'selenium', 'lxml',
        'pandas', 'numpy', 'python-dotenv'
    ]
    
    missing = []
    for package in required:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    if missing:
        return False, f"Missing packages: {', '.join(missing)}"
    return True, "✓ All dependencies installed"

def check_chrome():
    """Check if Chrome is installed"""
    chrome_paths = {
        'Windows': [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        ],
        'Darwin': [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        ],
        'Linux': [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium-browser"
        ]
    }
    
    system = platform.system()
    if system in chrome_paths:
        for path in chrome_paths[system]:
            if os.path.exists(path):
                return True, f"✓ Chrome found at: {path}"
    
    # Try which command on Unix-like systems
    if system in ['Darwin', 'Linux']:
        try:
            result = subprocess.run(['which', 'google-chrome'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return True, f"✓ Chrome found at: {result.stdout.strip()}"
        except:
            pass
    
    return False, "Chrome not found. Please install Google Chrome"

def check_chrome_driver():
    """Check if Chrome driver is available"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
        
        # Try to get driver
        driver_path = ChromeDriverManager().install()
        
        # Test it
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        driver.quit()
        
        return True, f"✓ Chrome driver working at: {driver_path}"
    except Exception as e:
        return False, f"Chrome driver issue: {str(e)}"

def check_directories():
    """Check if required directories exist"""
    base_dir = Path(__file__).resolve().parent
    required_dirs = [
        'data/raw',
        'data/processed',
        'data/cache',
        'backend/scrapers'
    ]
    
    missing = []
    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        if not full_path.exists():
            missing.append(dir_path)
    
    if missing:
        return False, f"Missing directories: {', '.join(missing)}"
    return True, "✓ All directories exist"

def check_config_files():
    """Check if configuration files exist"""
    base_dir = Path(__file__).resolve().parent
    files_to_check = {
        'backend/config.py': 'Configuration file',
        '.env': 'Environment variables file',
        'data/raw/instagram_handles.txt': 'Instagram handles file'
    }
    
    missing = []
    warnings = []
    
    for file_path, description in files_to_check.items():
        full_path = base_dir / file_path
        if not full_path.exists():
            if file_path == '.env':
                warnings.append(f"{description} not found (optional but recommended)")
            else:
                missing.append(f"{description} ({file_path})")
    
    if missing:
        return False, f"Missing files: {', '.join(missing)}"
    elif warnings:
        return True, f"✓ Core files exist. Warnings: {'; '.join(warnings)}"
    return True, "✓ All configuration files exist"

def check_instagram_credentials():
    """Check if Instagram credentials are configured"""
    try:
        from backend.config import INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD
        
        if not INSTAGRAM_USERNAME or not INSTAGRAM_PASSWORD:
            return False, "Instagram credentials not set in config.py or .env"
        
        if INSTAGRAM_USERNAME == "your_instagram_username":
            return False, "Instagram credentials not updated (still using template values)"
        
        return True, "✓ Instagram credentials configured"
    except ImportError:
        return False, "Cannot import config.py"

def check_network():
    """Check network connectivity"""
    import requests
    
    test_urls = [
        ('https://www.instagram.com', 'Instagram'),
        ('https://www.google.com', 'Google'),
    ]
    
    failed = []
    for url, name in test_urls:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code != 200:
                failed.append(f"{name} (status: {response.status_code})")
        except Exception as e:
            failed.append(f"{name} (error: {type(e).__name__})")
    
    if failed:
        return False, f"Network issues: {', '.join(failed)}"
    return True, "✓ Network connectivity OK"

def check_existing_data():
    """Check for existing scraped data"""
    base_dir = Path(__file__).resolve().parent
    data_files = {
        'data/raw/instagram_profiles.json': 'Instagram profiles',
        'data/raw/website_packages.json': 'Website packages'
    }
    
    found = []
    for file_path, description in data_files.items():
        full_path = base_dir / file_path
        if full_path.exists():
            try:
                with open(full_path, 'r') as f:
                    data = json.load(f)
                    count = len(data)
                    found.append(f"{description}: {count} entries")
            except:
                found.append(f"{description}: exists but unreadable")
    
    if found:
        return True, f"✓ Existing data: {'; '.join(found)}"
    return True, "No existing data found (this is normal for first run)"

def run_diagnostics():
    """Run all diagnostic checks"""
    print("=== TrippyPick Diagnostics ===\n")
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Chrome Browser", check_chrome),
        ("Chrome Driver", check_chrome_driver),
        ("Directories", check_directories),
        ("Config Files", check_config_files),
        ("Instagram Credentials", check_instagram_credentials),
        ("Network Connectivity", check_network),
        ("Existing Data", check_existing_data)
    ]
    
    all_passed = True
    
    for name, check_func in checks:
        print(f"\nChecking {name}...")
        try:
            passed, message = check_func()
            if passed:
                print(f"  {message}")
            else:
                print(f"  ✗ {message}")
                all_passed = False
        except Exception as e:
            print(f"  ✗ Error during check: {e}")
            all_passed = False
    
    print("\n" + "="*40)
    if all_passed:
        print("✓ All checks passed! You're ready to scrape.")
        print("\nRun: python app.py --all")
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        print("\nFor setup help, run: python setup.py")
    
    return all_passed

if __name__ == "__main__":
    success = run_diagnostics()
    sys.exit(0 if success else 1)