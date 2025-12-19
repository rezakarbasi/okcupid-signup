"""
OkCupid Automation - Main automation class.
Handles sign-up and login processes with organized methods.
"""

import asyncio
import random
import string
from pathlib import Path
from typing import Optional
from playwright.async_api import async_playwright, TimeoutError as PWTimeoutError, Page, Browser, BrowserContext
from playwright_stealth import Stealth

try:
    import smspool_auto
except ImportError:
    print("Error: 'smspool_auto' library not found.")
    raise

import config


class OkCupidAutomation:
    """Main class for OkCupid automation."""
    
    def __init__(self):
        """Initialize automation with values from config.py"""
        # Browser configuration from config
        self.start_url = config.START_URL
        self.proxy = config.PROXY  # Can be None to disable proxy
        self.headless = config.HEADLESS
        self.storage_file = config.STORAGE_FILE
        
        # SMS configuration from config
        self.sms_country = config.SMS_CONFIG["country"]
        self.sms_service_id = config.SMS_CONFIG["service_id"]
        
        # Sign-up configuration from config
        signup = config.SIGNUP_CONFIG
        self.email_base = signup["email_base"]
        self.email_domain = signup["email_domain"]
        self.email_max_dots = signup["email_max_dots"]
        self.first_name = signup["first_name"]
        self.country_name = signup["country"]
        self.country_code = signup["country_code"]
        self.city = signup["city"]
        self.gender = signup["gender"]
        self.interested_in = signup["interested_in"]
        self.birth_year_min = signup["birth_year_min"]
        self.birth_year_max = signup["birth_year_max"]
        self.birth_month_min = signup["birth_month_min"]
        self.birth_month_max = signup["birth_month_max"]
        self.birth_day_min = signup["birth_day_min"]
        self.birth_day_max = signup["birth_day_max"]
        self.password_length = signup["password_length"]
        self.self_summary = signup["self_summary"]
        self.profile_image = signup["profile_image_path"]
        self.dating_goal = signup["dating_goal"]
        
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
    
    # ==================== Utility Methods ====================
    
    @staticmethod
    def random_dotted_string(s: str, max_dots: int = None) -> str:
        """Insert random underscores into a string."""
        if max_dots is None:
            max_dots = len(s) // 3
        num_dots = random.randint(1, max_dots)
        positions = sorted(random.sample(range(0, len(s)), num_dots))
        result = []
        for i, ch in enumerate(s):
            result.append(ch)
            if i + 1 in positions:
                result.append('_')
        return ''.join(result)
    
    @staticmethod
    def generate_random_password(length: int = 16) -> str:
        """Generate a random password."""
        chars = string.ascii_letters + string.digits + string.punctuation
        return ''.join(random.choice(chars) for _ in range(length))
    
    def generate_random_dob(self) -> dict:
        """Generate random date of birth using config values."""
        return {
            'year': str(random.randint(self.birth_year_min, self.birth_year_max)),
            'month': str(random.randint(self.birth_month_min, self.birth_month_max)),
            'day': str(random.randint(self.birth_day_min, self.birth_day_max))
        }
    
    async def select_random_radio(self) -> None:
        """Select a random radio button from visible options."""
        try:
            await self.page.get_by_role("radio").first.wait_for(timeout=10000)
            radio_buttons = self.page.get_by_role("radio")
            count = await radio_buttons.count()
            if count > 0:
                random_index = random.randint(0, count - 1)
                selected_radio = radio_buttons.nth(random_index)
                label_text = await selected_radio.get_attribute("name") or f"Option {random_index + 1}"
                print(f"  ...selecting random option (out of {count}): \"{label_text}\"")
                await selected_radio.click()
            else:
                print("  ...no radio buttons found to select.")
        except Exception as e:
            print(f"  ...error selecting random radio: {e}")
    
    async def select_country_from_dropdown(self) -> bool:
        """Select country from dropdown using multiple fallback methods."""
        print(f"Selecting Country: {self.country_name}...")
        country_field = self.page.get_by_label('Country')
        await country_field.click()
        await self.page.wait_for_timeout(800)
        
        country_selected = False
        
        # Method 1: select_option with country code
        if not country_selected and self.country_code:
            try:
                await country_field.select_option(self.country_code, timeout=2000)
                print(f"✓ Selected {self.country_name} using select_option with '{self.country_code}' code.")
                country_selected = True
            except Exception as e1:
                print(f"  Method 1 (select_option '{self.country_code}') failed: {e1}")
        
        # Method 2: select_option with country name
        if not country_selected:
            try:
                await country_field.select_option(label=self.country_name, timeout=2000)
                print(f"✓ Selected {self.country_name} using select_option with '{self.country_name}' label.")
                country_selected = True
            except Exception as e2:
                print(f"  Method 2 (select_option label) failed: {e2}")
        
        # Method 3: Click by text (exact then partial)
        if not country_selected:
            try:
                await self.page.wait_for_timeout(500)
                country_option = self.page.get_by_text(self.country_name, exact=True).first
                await country_option.wait_for(state='visible', timeout=2000)
                await country_option.click()
                print(f"✓ Selected {self.country_name} using exact text match.")
                country_selected = True
            except Exception as e3:
                try:
                    country_option = self.page.get_by_text(self.country_name, exact=False).first
                    await country_option.wait_for(state='visible', timeout=2000)
                    await country_option.click()
                    print(f"✓ Selected {self.country_name} using partial text match.")
                    country_selected = True
                except Exception:
                    print(f"  Method 3 (text match) failed: {e3}")
        
        # Method 4: role="option"
        if not country_selected:
            try:
                await self.page.wait_for_timeout(500)
                country_option = self.page.get_by_role("option", name=self.country_name, exact=False).first
                await country_option.wait_for(state='visible', timeout=2000)
                await country_option.click()
                print(f"✓ Selected {self.country_name} using role='option' method.")
                country_selected = True
            except Exception as e4:
                print(f"  Method 4 (role option) failed: {e4}")
        
        # Method 5: locator with text variants
        if not country_selected:
            try:
                await self.page.wait_for_timeout(500)
                for text_variant in [self.country_name, self.country_code, f"{self.country_name} ({self.country_code})"]:
                    if not text_variant:
                        continue
                    try:
                        country_option = self.page.locator(f'text={text_variant}').first
                        await country_option.wait_for(state='visible', timeout=1500)
                        await country_option.click()
                        print(f"✓ Selected {self.country_name} using locator with '{text_variant}'.")
                        country_selected = True
                        break
                    except:
                        continue
            except Exception as e5:
                print(f"  Method 5 (locator text) failed: {e5}")
        
        if country_selected:
            await self.page.wait_for_timeout(1000)
        return country_selected
    
    def get_main_page_next_button(self):
        """Get the NEXT button on the main page (not in dialogs)."""
        return self.page.locator('*:not(div[role="dialog"])').get_by_role("button", name="NEXT").first
    
    # ==================== Browser Management ====================
    
    
    async def save_storage_state(self) -> None:
        """Save browser storage state to file."""
        if not self.context:
            raise RuntimeError("Browser context not initialized")
        print(f"Saving storage state to {self.storage_file}...")
        await self.context.storage_state(path=str(self.storage_file))
        print("Storage state saved successfully.")
    
    # ==================== Sign-up Steps ====================
    
    async def step_join_okcupid(self) -> None:
        """Step 1: Click join button."""
        await self.page.get_by_role("link", name="JOIN OkCupid").first.click()
    
    async def step_enter_email_and_name(self) -> None:
        """Step 2: Enter email and first name."""
        print("Entering user details...")
        email = self.random_dotted_string(self.email_base, self.email_max_dots) + self.email_domain
        print(f"Generated email: {email}")
        
        await self.page.get_by_role("textbox", name="Enter your email").click()
        await self.page.get_by_role("textbox", name="Enter your email").fill(email)
        await self.page.get_by_role("button", name="NEXT").click()
        
        await self.page.get_by_role("textbox", name="First name").click()
        await self.page.get_by_role("textbox", name="First name").fill(self.first_name)
        await self.page.get_by_role("button", name="NEXT").click()
    
    async def step_enter_location(self) -> None:
        """Step 3: Select country and enter city."""
        print("Filling location information...")
        
        country_selected = await self.select_country_from_dropdown()
        if not country_selected:
            await self.page.screenshot(path="country_dropdown_debug.png")
            print("  Screenshot saved to: country_dropdown_debug.png")
        
        await self.page.get_by_role("textbox", name="City").click()
        await self.page.get_by_role("textbox", name="City").fill(self.city)
        await self.page.wait_for_timeout(2000)
        
        # Handle city suggestion
        try:
            xpath_selector = "//select[@id='suggestion']/option[2]"
            link = self.page.locator(xpath_selector)
            value = await link.get_attribute("value")
            print(f"City suggestion value: {value}")
            await self.page.get_by_label(f'Matches for {self.city}').select_option(str(value))
        except Exception as e:
            print(f"  City suggestion handling skipped: {e}")
        
        await self.page.get_by_role("button", name="NEXT").click()
    
    async def step_select_gender_and_preferences(self) -> None:
        """Step 4: Select gender and dating preferences."""
        print("Filling gender and preferences...")
        await self.page.get_by_role("radio", name=self.gender, exact=True).click()
        await self.page.get_by_role("button", name="NEXT").click()
        await self.page.get_by_role("checkbox", name=self.interested_in, exact=True).click()
        await self.page.get_by_role("button", name="NEXT").click()
    
    async def step_enter_date_of_birth(self) -> None:
        """Step 5: Enter random date of birth."""
        print("Filling date of birth...")
        dob = self.generate_random_dob()
        print(f"Random DOB: {dob['day']}/{dob['month']}/{dob['year']}")
        
        await self.page.get_by_role("spinbutton", name="Month").click()
        await self.page.get_by_role("spinbutton", name="Month").fill(dob["month"])
        await self.page.get_by_role("spinbutton", name="Day").fill(dob["day"])
        await self.page.get_by_role("spinbutton", name="Year").click()
        await self.page.get_by_role("spinbutton", name="Year").fill(dob["year"])
        await self.page.get_by_role("button", name="NEXT").click()
    
    async def step_enter_password(self) -> None:
        """Step 6: Enter randomly generated password."""
        print("Filling password...")
        password = self.generate_random_password(self.password_length)
        print(f"Generated password: {password}")
        
        await self.page.get_by_role("textbox", name="Enter your password. 8").click()
        await self.page.get_by_role("textbox", name="Enter your password. 8").fill(password)
        await self.page.get_by_role("button", name="NEXT").click()
    
    async def step_select_dating_goal_and_cookies(self) -> None:
        """Step 7: Select dating goal and handle cookie banner."""
        print("Filling dating goal...")
        await self.page.get_by_role("checkbox", name=self.dating_goal).click()
        
        # Handle cookie banner
        print("Handling OneTrust cookie banner...")
        try:
            button_group = self.page.locator("#onetrust-button-group")
            await button_group.wait_for(state="visible", timeout=5000)
            accept_button = button_group.locator("#onetrust-accept-btn-handler")
            if await accept_button.count() == 0:
                accept_button = button_group.get_by_role("button", name="Accept All Cookies")
            print("Clicking 'Accept All' on cookie banner...")
            await accept_button.click()
            await button_group.wait_for(state="hidden", timeout=3000)
            print("Cookie banner hidden.")
        except PWTimeoutError:
            print("Cookie banner not found or already dismissed. Continuing...")
        except Exception as e:
            print(f"Error handling cookie banner: {e}. Continuing...")
        
        await self.get_main_page_next_button().click()
        await self.get_main_page_next_button().click()
    
    async def step_upload_profile_image(self) -> None:
        """Step 8: Upload profile image."""
        print(f"Uploading profile image: {self.profile_image}...")
        image_file = Path(self.profile_image)
        if not image_file.exists():
            raise FileNotFoundError(f"Profile image not found: {self.profile_image}")
        
        await self.page.get_by_role("button", name="Upload image +").click()
        
        async with self.page.expect_file_chooser() as fc_info:
            await self.page.get_by_role("button", name="Upload image from your").click()
        
        file_chooser = await fc_info.value
        await file_chooser.set_files(str(image_file))
        
        xpath_selector = '//button[@data-cy="photoUploader.doneButton"]'
        await self.page.wait_for_selector(xpath_selector, strict=True)
        await self.page.click(xpath_selector)
        await self.page.wait_for_timeout(2000)
        print("Image uploaded successfully.")
    
    async def step_enter_self_summary(self) -> None:
        """Step 9: Enter self-summary/bio."""
        print("Filling self-summary...")
        # Fill the self-summary text (NEXT was already clicked after image upload)
        await self.page.get_by_role("textbox", name="My Self-Summary").fill(self.self_summary)
        # Wait for the button to become enabled after text is filled
        # Use data-cy selector to find the button and wait for it to be enabled
        await self.page.wait_for_function(
            """() => {
                const button = document.querySelector('button[data-cy="onboarding.nextButton"]');
                return button && !button.disabled;
            }""",
            timeout=15000
        )
        # Click NEXT to proceed
        await self.get_main_page_next_button().click()
    
    async def step_answer_questions(self) -> int:
        """Step 10: Answer profile questions randomly."""
        print("Answering questions randomly...")
        await self.page.get_by_role("button", name="GET STARTED").click()
        
        question_count = 0
        while True:
            print(f"Checking for question {question_count + 1}...")
            try:
                await self.page.get_by_role("radio").first.wait_for(state="visible", timeout=3000)
                question_count += 1
                print(f"Answering question {question_count}...")
                await self.select_random_radio()
                await self.page.wait_for_timeout(1500)
            except PWTimeoutError:
                print("No more radio buttons found. Assuming questions are finished.")
                try:
                    await self.page.get_by_role("textbox", name="Enter your phone number").wait_for(
                        state="visible", timeout=1000
                    )
                    print("Phone number textbox is visible. Breaking question loop.")
                    break
                except PWTimeoutError:
                    print("Phone number box not visible. Breaking loop anyway.")
                    break
            except Exception as e:
                print(f"An unexpected error occurred during question loop: {e}. Breaking.")
                break
        
        print(f"Finished answering {question_count} questions.")
        return question_count
    
    async def step_phone_verification(self) -> None:
        """Step 11: Handle phone number verification via SMS."""
        print("Handling phone verification...")
        
        # Purchase phone number
        try:
            print("Purchasing phone number via smspool...")
            info = await asyncio.to_thread(
                smspool_auto.purchase_okcupid_number,
                self.sms_country,
                self.sms_service_id
            )
            
            if "phone_national" in info and "order_id" in info:
                phone_number = info["phone_national"]
                order_id = info["order_id"]
                print(f"Got number: {phone_number} (Order ID: {order_id})")
                await self.page.get_by_role("textbox", name="Enter your phone number").fill(phone_number)
            else:
                raise Exception(f"smspool response missing data. Got: {info}")
        except Exception as e:
            print(f"Error purchasing phone number: {e}")
            raise
        
        # Submit phone number
        print("Submitting phone number...")
        await self.get_main_page_next_button().click()
        
        # Wait for SMS code
        try:
            if not order_id:
                raise Exception("order_id was not set. Cannot wait for SMS.")
            
            print(f"Waiting for SMS for order ID: {order_id}...")
            print("Running smspool_auto.wait_for_sms... (This will block)")
            result = smspool_auto.wait_for_sms(order_id)
            print("...smspool_auto.wait_for_sms finished.")
            
            if "sms_code" in result:
                sms_code = result["sms_code"]
                print(f"Got code: {sms_code}")
                
                if len(sms_code) == 6:
                    print("Entering 6-digit code...")
                    spin_buttons = self.page.get_by_role("spinbutton")
                    for i in range(6):
                        await spin_buttons.nth(i).fill(sms_code[i])
                    print("Code entered.")
                else:
                    raise Exception(f"SMS code '{sms_code}' is not 6 digits.")
            else:
                raise Exception(f"smspool response missing sms_code. Got: {result}")
        except Exception as e:
            print(f"Error waiting for SMS: {e}")
            raise
        
        # Submit SMS code
        print("Clicking 'NEXT' button after entering SMS code...")
        code_form = self.page.get_by_role("spinbutton").first.locator("xpath=ancestor::form")
        await code_form.get_by_role("button", name="NEXT").click()
        print("Clicked 'NEXT' on code form.")
        
        print("Clicking 'MAYBE LATER'...")
        await self.page.get_by_role("button", name="MAYBE LATER").click()
    
    # ==================== Main Flows ====================
    
    async def perform_signup(self) -> None:
        """Perform complete sign-up process."""
        print("Starting automated sign-up...")
        
        try:
            await self.step_join_okcupid()
            await self.step_enter_email_and_name()
            await self.step_enter_location()
            await self.step_select_gender_and_preferences()
            await self.step_enter_date_of_birth()
            await self.step_enter_password()
            await self.step_select_dating_goal_and_cookies()
            await self.step_upload_profile_image()
            await self.get_main_page_next_button().click()
            await self.step_enter_self_summary()
            await self.step_answer_questions()
            await self.step_phone_verification()
            
            print("Sign-up complete!")
            
        except PWTimeoutError as e:
            print(f"Script timed out. An element was not found or page took too long: {e}")
            try:
                await self.page.screenshot(path="timeout_error_screenshot.png")
                print("Saved screenshot to timeout_error_screenshot.png")
            except:
                pass
            raise
        except Exception as e:
            print(f"An error occurred: {e}")
            try:
                await self.page.screenshot(path="error_screenshot.png")
                print("Saved screenshot to error_screenshot.png")
            except:
                pass
            raise
    
    async def signup_flow(self) -> None:
        """Complete sign-up flow with browser management."""
        print("=" * 60)
        print("OKCUPID AUTOMATED SIGN-UP")
        print("=" * 60)
        
        # Use async context manager for playwright (like original code)
        async with Stealth().use_async(async_playwright()) as p:
            browser_args = {}
            if self.proxy is not None:
                print(f"Using proxy: {self.proxy['server']}")
                browser_args["proxy"] = self.proxy
            else:
                print("Running without proxy.")

            self.browser = await p.chromium.launch(headless=self.headless, **browser_args)
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            self.page.set_default_timeout(30000)

            print(f"Navigating to {self.start_url}...")
            await self.page.goto(self.start_url)
            print("Site loaded.")
            
            try:
                await self.perform_signup()
                
                # Save storage state
                await self.page.wait_for_timeout(5000)
                await self.page.goto(self.start_url)
                await self.page.wait_for_timeout(5000)
                await self.save_storage_state()
                
                print("\n" + "=" * 60)
                print("SIGN-UP COMPLETE!")
                print(f"Storage state saved to: {self.storage_file}")
                print("You can now use this file to log in automatically.")
                print("=" * 60)
            finally:
                await self.context.close()
                await self.browser.close()
                print("Browser closed.")
    
    async def login_flow(self) -> None:
        """Login flow using saved storage state."""
        print("=" * 60)
        print("OKCUPID AUTOMATED LOGIN")
        print("=" * 60)
        
        if not self.storage_file.exists():
            raise FileNotFoundError(f"Storage file not found: {self.storage_file}")
        
        # Use async context manager for playwright (like original code)
        async with Stealth().use_async(async_playwright()) as p:
            browser_args = {}
            if self.proxy is not None:
                print(f"Using proxy: {self.proxy['server']}")
                browser_args["proxy"] = self.proxy
            else:
                print("Running without proxy.")

            self.browser = await p.chromium.launch(headless=self.headless, **browser_args)
            self.context = await self.browser.new_context(storage_state=str(self.storage_file))
            self.page = await self.context.new_page()
            self.page.set_default_timeout(30000)

            print(f"Navigating to {self.start_url}...")
            await self.page.goto(self.start_url)
            print("Page loaded with cached state.")
            print(f"Cookies: {len(await self.context.cookies())} cookies loaded")
            print("\nBrowser is open. You can interact with the page.")
            print("Press Ctrl+C to close the browser.")
            
            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print("\nClosing browser...")
            finally:
                await self.browser.close()
                print("Browser closed.")

