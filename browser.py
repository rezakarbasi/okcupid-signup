"""
Browser setup and management utilities.
"""

from pathlib import Path
from typing import Optional, Dict, Tuple
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from playwright_stealth import Stealth

import config


async def create_browser(headless: bool = None, proxy: Optional[Dict[str, str]] = None) -> Tuple[Browser, BrowserContext, Page]:
    """
    Create a stealthed browser instance with optional proxy.
    
    Args:
        headless: Whether to run browser in headless mode (defaults to config.HEADLESS)
        proxy: Optional proxy configuration (defaults to config.PROXY)
    
    Returns:
        Tuple of (browser, context, page)
    """
    if headless is None:
        headless = config.HEADLESS
    if proxy is None:
        proxy = config.PROXY
    
    print("Starting stealth browser...")
    playwright = None
    
    async with Stealth().use_async(async_playwright()) as p:
        playwright = p
        browser_args = {}
        
        if proxy:
            print(f"Using proxy: {proxy['server']}")
            browser_args["proxy"] = proxy

        browser = await p.chromium.launch(headless=headless, **browser_args)
        context = await browser.new_context()
        page = await context.new_page()
        page.set_default_timeout(config.BROWSER_TIMEOUT)

        print(f"Navigating to {config.START_URL}...")
        await page.goto(config.START_URL)
        print("Site loaded.")
        
        return browser, context, page


async def load_browser_with_storage(storage_file: Path = None, headless: bool = None, 
                                     proxy: Optional[Dict[str, str]] = None) -> Tuple[Browser, BrowserContext, Page]:
    """
    Create a browser instance and load saved storage state (for login).
    
    Args:
        storage_file: Path to storage state file (defaults to config.STORAGE_FILE)
        headless: Whether to run browser in headless mode (defaults to config.HEADLESS)
        proxy: Optional proxy configuration (defaults to config.PROXY)
    
    Returns:
        Tuple of (browser, context, page)
    
    Raises:
        FileNotFoundError: If storage file doesn't exist
    """
    if storage_file is None:
        storage_file = config.STORAGE_FILE
    if headless is None:
        headless = config.HEADLESS
    if proxy is None:
        proxy = config.PROXY
    
    if not storage_file.exists():
        raise FileNotFoundError(f"Storage file not found: {storage_file}")
    
    print("Starting browser with saved storage state...")
    playwright = None
    
    async with Stealth().use_async(async_playwright()) as p:
        playwright = p
        browser_args = {}
        
        if proxy:
            print(f"Using proxy: {proxy['server']}")
            browser_args["proxy"] = proxy

        browser = await p.chromium.launch(headless=headless, **browser_args)
        
        # Load the saved storage state (cookies, localStorage, etc.)
        context = await browser.new_context(storage_state=str(storage_file))
        page = await context.new_page()
        page.set_default_timeout(config.BROWSER_TIMEOUT)

        print(f"Navigating to {config.START_URL}...")
        await page.goto(config.START_URL)
        print("Page loaded with cached state.")
        
        return browser, context, page


async def save_storage_state(context: BrowserContext, storage_file: Path = None) -> None:
    """
    Save browser storage state (cookies, localStorage, etc.) to file.
    
    Args:
        context: Browser context to save state from
        storage_file: Path to save storage state (defaults to config.STORAGE_FILE)
    """
    if storage_file is None:
        storage_file = config.STORAGE_FILE
    
    print(f"Saving storage state to {storage_file}...")
    await context.storage_state(path=str(storage_file))
    print("Storage state saved successfully.")


async def close_browser(browser: Browser) -> None:
    """
    Close browser instance.
    
    Args:
        browser: Browser instance to close
    """
    await browser.close()
    print("Browser closed.")

