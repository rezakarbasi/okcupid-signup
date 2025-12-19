"""
OkCupid login module using saved storage state.
This module loads a previously saved storage state file to log in automatically.
"""

from pathlib import Path
from typing import Tuple
from playwright.async_api import BrowserContext, Browser, Page

import config
from browser import load_browser_with_storage, close_browser


async def login_with_storage(storage_file: Path = None) -> Tuple[Browser, BrowserContext, Page]:
    """
    Login to OkCupid using saved storage state.
    
    Args:
        storage_file: Path to storage state file (defaults to config.STORAGE_FILE)
    
    Returns:
        Tuple of (browser, context, page) for further use
    
    Raises:
        FileNotFoundError: If storage file doesn't exist
    """
    if storage_file is None:
        storage_file = config.STORAGE_FILE
    
    browser, context, page = await load_browser_with_storage(storage_file)
    
    print("Login successful! You are now logged in using saved session.")
    print(f"Cookies: {len(await context.cookies())} cookies loaded")
    
    return browser, context, page


async def verify_login(context: BrowserContext) -> bool:
    """
    Verify if login was successful by checking cookies.
    
    Args:
        context: Browser context to check
    
    Returns:
        True if logged in (has cookies), False otherwise
    """
    cookies = await context.cookies()
    return len(cookies) > 0
