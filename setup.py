#!/usr/bin/env python3
"""
Setup script for TrippyPick project
Installs dependencies and sets up Chrome driver
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(command):
    """Run a shell command"""
    try:
        subprocess.run(command, shell=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        return False

def setup_project():
    """Set up the TrippyPick project"""
    print("=== TrippyPick Setup ===\n")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 7):
        print("Error: Python 3.7 or higher is required")
        sys.exit(1)
    
    print(f"✓ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Install pip dependencies
    print("\n1. Installing Python dependencies...")
    if run_command(f"{sys.executable} -m pip install --upgrade pip"):
        print("✓ pip updated")
    
    if run_command(f"{sys.executable} -m pip install -r requirements.txt"):
        print("✓ Dependencies installed")
    else:
        print("✗ Failed to install dependencies")
        sys.exit(1)
    
    # Install Chrome driver using webdriver-manager
    print("\n2. Setting up Chrome driver...")
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        
        # This will download and cache the Chrome driver
        driver_path = ChromeDriverManager().install()
        print(f"✓ Chrome driver installed at: {driver_path}")
        
        # Test Chrome driver
        print("\n3. Testing Chrome driver...")
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        driver.quit()
        print("✓ Chrome driver working")
        
    except Exception as e:
        print(f"✗ Chrome driver setup failed: {e}")
        print("\nPlease install Chrome/Chromium and try again")
    
    # Create necessary directories
    print("\n4. Creating project directories...")
    base_dir = Path(__file__).resolve().parent
    dirs_to_create = [
        'data/raw',
        'data/processed',
        'data/cache',
        'logs',
        'output'
    ]
    
    for dir_path in dirs_to_create:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created {dir_path}")
    
    # Create .env file if it doesn't exist
    print("\n5. Setting up environment file...")
    env_file = base_dir / '.env'
    if not env_file.exists():
        env_template = """# Instagram Credentials
INSTAGRAM_USERNAME=your_instagram_username
INSTAGRAM_PASSWORD=your_instagram_password

# Scraping Settings
HEADLESS_BROWSER=false
USE_SELENIUM_FOR_WEBSITES=true
"""
        env_file.write_text(env_template)
        print("✓ Created .env file (please update with your credentials)")
    else:
        print("✓ .env file already exists")
    
    # Create sample Instagram handles file
    print("\n6. Creating sample Instagram handles file...")
    handles_file = base_dir / 'data' / 'raw' / 'instagram_handles.txt'
    if not handles_file.exists():
        sample_handles = """# Sample travel Instagram handles
# Add one handle per line (without @)
wanderon.in
tripzygo.official
thrillophilia
makemytrip
yatra_com
traveltriangle
goibibo
nomadsofblr
adventurebuddha
holidaysbyatlas
conceptholidayz
"""
        handles_file.write_text(sample_handles)
        print("✓ Created sample Instagram handles file")
    else:
        print("✓ Instagram handles file already exists")
    
    print("\n=== Setup Complete! ===")
    print("\nNext steps:")
    print("1. Update the .env file with your Instagram credentials")
    print("2. Add more Instagram handles to data/raw/instagram_handles.txt")
    print("3. Run: python app.py --all")
    
    # Platform-specific notes
    if platform.system() == "Linux":
        print("\nNote: On Linux, you may need to install Chrome:")
        print("  sudo apt-get install google-chrome-stable")
    elif platform.system() == "Darwin":
        print("\nNote: On macOS, you may need to install Chrome:")
        print("  brew install --cask google-chrome")

if __name__ == "__main__":
    setup_project()