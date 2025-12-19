"""
Configuration file for OkCupid automation.
All static variables for sign-up and login are defined here.
"""

from pathlib import Path
from typing import Optional, Dict

# ==================== Browser Configuration ====================
START_URL = "https://www.okcupid.com/"
HEADLESS = False  # Set to True to run browser in background
BROWSER_TIMEOUT = 30000  # Default timeout in milliseconds

# Optional proxy configuration
# Default: Uses socks5 proxy at 127.0.0.1:2070
# To disable proxy, set to: PROXY = None
# To use a different proxy, set to: PROXY = {"server": "socks5://your-proxy:port"}
PROXY: Optional[Dict[str, str]] = {"server": "socks5://127.0.0.1:2070"}

# Storage state file path (saved after sign-up, used for login)
STORAGE_FILE = Path("storage_state.json")

# ==================== Sign-up Configuration ====================

# User Profile Information
SIGNUP_CONFIG = {
    # Email configuration
    "email_base": "test.mail.okcupid",  # Base email string (will be modified with random characters)
    "email_domain": "@gmail.com",
    "email_max_dots": 6,  # Maximum number of random characters to insert
    
    # Personal Information
    "first_name": "Jack",
    "country": "Finland",  # Country name as it appears in dropdown
    "country_code": "FI",  # ISO country code (optional, for native select elements)
    "city": "Helsinki",
    
    # Gender and Preferences
    "gender": "Man",  # Options: "Man", "Woman", "Non-binary", etc.
    "interested_in": "Men",  # Options: "Men", "Women", "Everyone", etc.
    
    # Date of Birth (will be randomized if None)
    "birth_year_min": 1987,
    "birth_year_max": 2005,
    "birth_month_min": 1,
    "birth_month_max": 12,
    "birth_day_min": 1,
    "birth_day_max": 28,  # Use 28 to avoid month-specific issues
    
    # Password (will be randomly generated if None)
    "password_length": 16,
    
    # Profile Details
    "dating_goal": "Long-term dating",  # Options: "Long-term dating", "Short-term dating", etc.
    "self_summary": "I'm handsome boy looking for pretty men",
    
    # Profile Image
    "profile_image_path": "./personface.jpg",  # Path to profile image file
}

# ==================== SMS Verification Configuration ====================
# This code uses SMSPool (https://smspool.net) for phone number verification (OTP)
# You need to sign up for SMSPool and get an API key from https://smspool.net
# All SMSPool settings are configured here - no environment variables needed
SMS_CONFIG = {
    "country": "US",  # Country code for SMS service (ISO format like "US", "NL", "GB")
    "service_id": 658,  # OkCupid service ID for SMSPool
    "api_key": "My-API-Key",  # Your SMSPool API key (get it from smspool.net dashboard)
    "calling_code": None,  # Optional: Country calling code (e.g., "1" for US, "44" for UK). If None, auto-detected.
    
    # SMS waiting & resend policy
    "poll_interval_sec": 6,  # How often to check for SMS (seconds)
    "max_wait_sec": 20 * 60,  # Maximum time to wait for SMS (20 minutes)
    "expire_grace_sec": 4 * 60,  # Grace period before expiration (4 minutes)
    "auto_resend": True,  # Automatically resend SMS if not received
    "resend_first_after": 90,  # Wait 90 seconds before first resend
    "resend_every": 120,  # Wait 120 seconds between resends
    "max_resends": 2,  # Maximum number of resend attempts
}

# ==================== Question Answering Configuration ====================
QUESTIONS_CONFIG = {
    "max_questions": None,  # None = answer all questions, or set a number
    "question_timeout": 3000,  # Timeout in ms to wait for next question
    "pause_between_answers": 1500,  # Pause in ms between answering questions
}

# ==================== Cookie Banner Configuration ====================
COOKIE_BANNER_CONFIG = {
    "enabled": True,  # Set to False to skip cookie banner handling
    "timeout": 5000,  # Timeout in ms to wait for cookie banner
    "button_group_selector": "#onetrust-button-group",
    "accept_button_selector": "#onetrust-accept-btn-handler",
    "accept_button_text": "Accept All Cookies",  # Fallback text search
}

# ==================== File Paths ====================
SCREENSHOT_DIR = Path("screenshots")
SCREENSHOT_DIR.mkdir(exist_ok=True)

ERROR_SCREENSHOT = SCREENSHOT_DIR / "error_screenshot.png"
TIMEOUT_SCREENSHOT = SCREENSHOT_DIR / "timeout_error_screenshot.png"
COUNTRY_DROPDOWN_DEBUG = SCREENSHOT_DIR / "country_dropdown_debug.png"

