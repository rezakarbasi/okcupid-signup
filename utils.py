"""
Utility functions for OkCupid automation.
"""

import random
import string
from playwright.async_api import Page, TimeoutError as PWTimeoutError


def random_dotted_string(base: str, max_dots: int = None) -> str:
    """
    Insert random underscores into a string to create variations.
    
    Args:
        base: The base string (e.g., "test.mail.okcupid")
        max_dots: Optional max number of underscores to insert (default: len(base)//3)
    
    Returns:
        String with random underscores inserted
    """
    if max_dots is None:
        max_dots = len(base) // 3

    num_dots = random.randint(1, max_dots)
    positions = sorted(random.sample(range(0, len(base)), num_dots))

    result = []
    for i, ch in enumerate(base):
        result.append(ch)
        if i + 1 in positions:
            result.append('_')
    return ''.join(result)


def generate_random_password(length: int = 16) -> str:
    """
    Generate a random password with letters, digits, and punctuation.
    
    Args:
        length: Length of the password
    
    Returns:
        Random password string
    """
    chars = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(chars) for _ in range(length))


def generate_random_dob(year_min: int, year_max: int, month_min: int = 1, 
                        month_max: int = 12, day_min: int = 1, day_max: int = 28) -> dict:
    """
    Generate random date of birth.
    
    Args:
        year_min: Minimum birth year
        year_max: Maximum birth year
        month_min: Minimum month (default: 1)
        month_max: Maximum month (default: 12)
        day_min: Minimum day (default: 1)
        day_max: Maximum day (default: 28)
    
    Returns:
        Dictionary with 'year', 'month', 'day' as strings
    """
    return {
        'year': str(random.randint(year_min, year_max)),
        'month': str(random.randint(month_min, month_max)),
        'day': str(random.randint(day_min, day_max))
    }


async def select_random_radio(page: Page, timeout: int = 10000) -> bool:
    """
    Finds all visible radio buttons for the current question,
    selects one at random, and clicks it.
    
    Args:
        page: Playwright page object
        timeout: Timeout in milliseconds
    
    Returns:
        True if a radio button was selected, False otherwise
    """
    try:
        # Wait for the first radio button to be visible
        await page.get_by_role("radio").first.wait_for(timeout=timeout)
        
        # Get all radio button locators on the page
        radio_buttons = page.get_by_role("radio")
        
        # Get the total count
        count = await radio_buttons.count()
        
        if count > 0:
            # Select a random index
            random_index = random.randint(0, count - 1)
            
            # Get the specific radio button
            selected_radio = radio_buttons.nth(random_index)
            
            # Get its name attribute for logging
            label_text = await selected_radio.get_attribute("name") or f"Option {random_index + 1}"
            print(f"  ...selecting random option (out of {count}): \"{label_text}\"")
            
            # Click the randomly selected radio button
            await selected_radio.click()
            return True
        else:
            print("  ...no radio buttons found to select.")
            return False
    except Exception as e:
        print(f"  ...error selecting random radio: {e}")
        return False


async def select_country_from_dropdown(page: Page, country_name: str, country_code: str = None) -> bool:
    """
    Select a country from a dropdown menu using multiple fallback methods.
    
    Args:
        page: Playwright page object
        country_name: Country name as it appears in the dropdown (e.g., "Finland")
        country_code: Optional ISO country code (e.g., "FI")
    
    Returns:
        True if country was selected successfully, False otherwise
    """
    print(f"Selecting Country: {country_name}...")
    country_field = page.get_by_label('Country')
    await country_field.click()
    await page.wait_for_timeout(800)  # Wait for dropdown to open
    
    country_selected = False
    
    # Method 1: If it's a native select element, use select_option with country code
    if not country_selected and country_code:
        try:
            await country_field.select_option(country_code, timeout=2000)
            print(f"✓ Selected {country_name} using select_option with '{country_code}' code.")
            country_selected = True
        except Exception as e1:
            print(f"  Method 1 (select_option '{country_code}') failed: {e1}")
    
    # Method 2: Try select_option with country name text
    if not country_selected:
        try:
            await country_field.select_option(label=country_name, timeout=2000)
            print(f"✓ Selected {country_name} using select_option with '{country_name}' label.")
            country_selected = True
        except Exception as e2:
            print(f"  Method 2 (select_option label) failed: {e2}")
    
    # Method 3: If it's a custom dropdown, click the option by text
    if not country_selected:
        try:
            await page.wait_for_timeout(500)
            # Try exact match first
            country_option = page.get_by_text(country_name, exact=True).first
            await country_option.wait_for(state='visible', timeout=2000)
            await country_option.click()
            print(f"✓ Selected {country_name} using exact text match.")
            country_selected = True
        except Exception as e3:
            print(f"  Method 3 (exact text) failed: {e3}")
            try:
                # Try partial match
                country_option = page.get_by_text(country_name, exact=False).first
                await country_option.wait_for(state='visible', timeout=2000)
                await country_option.click()
                print(f"✓ Selected {country_name} using partial text match.")
                country_selected = True
            except Exception as e3b:
                print(f"  Method 3b (partial text) failed: {e3b}")
    
    # Method 4: Try using role="option" for dropdown items
    if not country_selected:
        try:
            await page.wait_for_timeout(500)
            country_option = page.get_by_role("option", name=country_name, exact=False).first
            await country_option.wait_for(state='visible', timeout=2000)
            await country_option.click()
            print(f"✓ Selected {country_name} using role='option' method.")
            country_selected = True
        except Exception as e4:
            print(f"  Method 4 (role option) failed: {e4}")
    
    # Method 5: Use locator with text containing country name
    if not country_selected:
        try:
            await page.wait_for_timeout(500)
            # Try different variations
            text_variants = [country_name]
            if country_code:
                text_variants.extend([country_code, f"{country_name} ({country_code})"])
            
            for text_variant in text_variants:
                try:
                    country_option = page.locator(f'text={text_variant}').first
                    await country_option.wait_for(state='visible', timeout=1500)
                    await country_option.click()
                    print(f"✓ Selected {country_name} using locator with '{text_variant}'.")
                    country_selected = True
                    break
                except:
                    continue
            if not country_selected:
                raise Exception("All text variants failed")
        except Exception as e5:
            print(f"  Method 5 (locator text) failed: {e5}")
    
    if not country_selected:
        print(f"⚠ WARNING: Could not select {country_name} automatically.")
        return False
    else:
        await page.wait_for_timeout(1000)  # Wait for selection to register
        return True


async def handle_cookie_banner(page: Page, config: dict) -> None:
    """
    Handle cookie consent banner if present.
    
    Args:
        page: Playwright page object
        config: Cookie banner configuration dictionary
    """
    if not config.get("enabled", True):
        return
    
    print("Handling cookie banner...")
    try:
        # Find the button group
        button_group = page.locator(config["button_group_selector"])
        await button_group.wait_for(state="visible", timeout=config["timeout"])
        
        # Find the "accept" button within that group
        accept_button = button_group.locator(config["accept_button_selector"])
        
        if await accept_button.count() == 0:
            # Fallback: try to find by text
            accept_button = button_group.get_by_role("button", name=config["accept_button_text"])
        
        print("Clicking 'Accept All' on cookie banner...")
        await accept_button.click()
        print("Clicked cookie banner button.")
        
        # Wait for the banner to disappear
        await button_group.wait_for(state="hidden", timeout=3000)
        print("Cookie banner hidden.")
    except PWTimeoutError:
        print("Cookie banner not found or already dismissed. Continuing...")
    except Exception as e:
        print(f"Error handling cookie banner: {e}. Continuing...")


def get_main_page_next_button(page: Page):
    """
    Get the NEXT button on the main page (not in dialogs).
    
    Args:
        page: Playwright page object
    
    Returns:
        Locator for the NEXT button
    """
    return page.locator('*:not(div[role="dialog"])').get_by_role("button", name="NEXT").first

