"""
OkCupid automated sign-up module.
This is the core sign-up automation logic.
"""

import asyncio
from pathlib import Path
from playwright.async_api import Page, TimeoutError as PWTimeoutError

import config
from utils import (
    random_dotted_string,
    generate_random_password,
    generate_random_dob,
    select_random_radio,
    select_country_from_dropdown,
    handle_cookie_banner,
    get_main_page_next_button,
)
from browser import save_storage_state

# Import SMS library
try:
    import smspool_auto
except ImportError:
    print("Error: 'smspool_auto' module not found.")
    print("Please ensure smspool_auto.py is in the same directory.")
    raise


async def fill_basic_info(page: Page, signup_config: dict) -> None:
    """
    Fill in basic user information (email, name).
    
    Args:
        page: Playwright page object
        signup_config: Sign-up configuration dictionary
    """
    print("Entering user details...")
    
    # Email
    email = random_dotted_string(
        signup_config["email_base"],
        signup_config["email_max_dots"]
    ) + signup_config["email_domain"]
    print(f"Generated email: {email}")
    
    await page.get_by_role("textbox", name="Enter your email").click()
    await page.get_by_role("textbox", name="Enter your email").fill(email)
    await page.get_by_role("button", name="NEXT").click()
    
    # First name
    await page.get_by_role("textbox", name="First name").click()
    await page.get_by_role("textbox", name="First name").fill(signup_config["first_name"])
    await page.get_by_role("button", name="NEXT").click()


async def fill_location(page: Page, signup_config: dict) -> None:
    """
    Fill in location information (country, city).
    
    Args:
        page: Playwright page object
        signup_config: Sign-up configuration dictionary
    """
    print("Filling location information...")
    
    # Select country
    country_selected = await select_country_from_dropdown(
        page,
        signup_config["country"],
        signup_config.get("country_code")
    )
    
    if not country_selected:
        print("⚠ Warning: Country selection may have failed. Continuing anyway...")
        await page.screenshot(path=str(config.COUNTRY_DROPDOWN_DEBUG))
        print(f"  Screenshot saved to: {config.COUNTRY_DROPDOWN_DEBUG}")
    
    # Fill city
    await page.get_by_role("textbox", name="City").click()
    await page.get_by_role("textbox", name="City").fill(signup_config["city"])
    await page.wait_for_timeout(2000)
    
    # Handle city suggestion dropdown if present
    try:
        xpath_selector = "//select[@id='suggestion']/option[2]"
        suggestion_link = page.locator(xpath_selector)
        value = await suggestion_link.get_attribute("value")
        if value:
            label_text = f"Matches for {signup_config['city']}"
            await page.get_by_label(label_text).select_option(str(value))
    except Exception as e:
        print(f"  City suggestion handling skipped: {e}")
    
    await get_main_page_next_button(page).click()


async def fill_gender_and_preferences(page: Page, signup_config: dict) -> None:
    """
    Fill in gender and dating preferences.
    
    Args:
        page: Playwright page object
        signup_config: Sign-up configuration dictionary
    """
    print("Filling gender and preferences...")
    
    # Gender
    await page.get_by_role("radio", name=signup_config["gender"], exact=True).click()
    await page.get_by_role("button", name="NEXT").click()
    
    # Interested in
    await page.get_by_role("checkbox", name=signup_config["interested_in"], exact=True).click()
    await page.get_by_role("button", name="NEXT").click()


async def fill_date_of_birth(page: Page, signup_config: dict) -> None:
    """
    Fill in date of birth (randomized).
    
    Args:
        page: Playwright page object
        signup_config: Sign-up configuration dictionary
    """
    print("Filling date of birth...")
    
    dob = generate_random_dob(
        signup_config["birth_year_min"],
        signup_config["birth_year_max"],
        signup_config["birth_month_min"],
        signup_config["birth_month_max"],
        signup_config["birth_day_min"],
        signup_config["birth_day_max"]
    )
    print(f"Random DOB: {dob['day']}/{dob['month']}/{dob['year']}")
    
    await page.get_by_role("spinbutton", name="Month").click()
    await page.get_by_role("spinbutton", name="Month").fill(dob["month"])
    await page.get_by_role("spinbutton", name="Day").fill(dob["day"])
    await page.get_by_role("spinbutton", name="Year").click()
    await page.get_by_role("spinbutton", name="Year").fill(dob["year"])
    await page.get_by_role("button", name="NEXT").click()


async def fill_password(page: Page, signup_config: dict) -> None:
    """
    Fill in password (randomly generated).
    
    Args:
        page: Playwright page object
        signup_config: Sign-up configuration dictionary
    """
    print("Filling password...")
    
    password = generate_random_password(signup_config["password_length"])
    print(f"Generated password: {password}")
    
    await page.get_by_role("textbox", name="Enter your password. 8").click()
    await page.get_by_role("textbox", name="Enter your password. 8").fill(password)
    await page.get_by_role("button", name="NEXT").click()


async def fill_dating_goal_and_handle_cookies(page: Page, signup_config: dict) -> None:
    """
    Fill in dating goal and handle cookie banner.
    
    Args:
        page: Playwright page object
        signup_config: Sign-up configuration dictionary
    """
    print("Filling dating goal...")
    
    await page.get_by_role("checkbox", name=signup_config["dating_goal"]).click()
    
    # Handle cookie banner
    await handle_cookie_banner(page, config.COOKIE_BANNER_CONFIG)
    
    # Click NEXT buttons (may need multiple clicks)
    await get_main_page_next_button(page).click()
    await page.wait_for_timeout(500)
    await get_main_page_next_button(page).click()


async def upload_profile_image(page: Page, image_path: str) -> None:
    """
    Upload profile image.
    
    Args:
        page: Playwright page object
        image_path: Path to image file
    """
    print(f"Uploading profile image: {image_path}...")
    
    image_file = Path(image_path)
    if not image_file.exists():
        raise FileNotFoundError(f"Profile image not found: {image_path}")
    
    await page.get_by_role("button", name="Upload image +").click()
    
    # Wait for file chooser
    async with page.expect_file_chooser() as fc_info:
        await page.get_by_role("button", name="Upload image from your").click()
    
    file_chooser = await fc_info.value
    await file_chooser.set_files(str(image_file))
    
    # Wait for upload and click done button
    xpath_selector = '//button[@data-cy="photoUploader.doneButton"]'
    await page.wait_for_selector(xpath_selector, strict=True)
    await page.click(xpath_selector)
    await page.wait_for_timeout(2000)
    
    print("Image uploaded successfully.")


async def fill_self_summary(page: Page, signup_config: dict) -> None:
    """
    Fill in self-summary/bio.
    
    Args:
        page: Playwright page object
        signup_config: Sign-up configuration dictionary
    """
    print("Filling self-summary...")
    
    await get_main_page_next_button(page).click()
    await page.wait_for_timeout(1000)
    
    await page.get_by_role("textbox", name="My Self-Summary").fill(signup_config["self_summary"])
    await get_main_page_next_button(page).click()


async def answer_profile_questions(page: Page, questions_config: dict) -> int:
    """
    Answer profile questions randomly.
    
    Args:
        page: Playwright page object
        questions_config: Questions configuration dictionary
    
    Returns:
        Number of questions answered
    """
    print("Answering profile questions...")
    await page.get_by_role("button", name="GET STARTED").click()
    
    question_count = 0
    max_questions = questions_config.get("max_questions")
    timeout = questions_config.get("question_timeout", 3000)
    pause = questions_config.get("pause_between_answers", 1500)
    
    while True:
        if max_questions and question_count >= max_questions:
            print(f"Reached maximum questions limit ({max_questions}).")
            break
        
        print(f"Checking for question {question_count + 1}...")
        try:
            # Check if a radio button is visible
            await page.get_by_role("radio").first.wait_for(state="visible", timeout=timeout)
            
            # Answer the question
            question_count += 1
            print(f"Answering question {question_count}...")
            await select_random_radio(page)
            
            # Brief pause for the next question to load
            await page.wait_for_timeout(pause)

        except PWTimeoutError:
            # No radio buttons found within timeout
            print("No more radio buttons found. Assuming questions are finished.")
            
            # Check if phone number box is visible (next step)
            try:
                await page.get_by_role("textbox", name="Enter your phone number").wait_for(
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


async def handle_phone_verification(page: Page, sms_config: dict) -> None:
    """
    Handle phone number verification via SMS.
    
    Args:
        page: Playwright page object
        sms_config: SMS configuration dictionary
    """
    print("Handling phone verification...")
    
    # Purchase phone number
    try:
        print("Purchasing phone number via smspool...")
        api_key = sms_config.get("api_key") or smspool_auto.API_KEY
        info = await asyncio.to_thread(
            smspool_auto.purchase_okcupid_number,
            sms_config["country"],
            sms_config["service_id"],
            api_key
        )
        
        if "phone_national" in info and "order_id" in info:
            phone_number = info["phone_national"]
            order_id = info["order_id"]
            print(f"Got number: {phone_number} (Order ID: {order_id})")
            
            # Fill the phone number
            await page.get_by_role("textbox", name="Enter your phone number").fill(phone_number)
        else:
            raise Exception(f"smspool response missing data. Got: {info}")

    except Exception as e:
        print(f"Error purchasing phone number: {e}")
        raise
    
    # Submit phone number
    print("Submitting phone number...")
    await get_main_page_next_button(page).click()
    
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
            
            # Enter the 6-digit code
            if len(sms_code) == 6:
                print("Entering 6-digit code...")
                spin_buttons = page.get_by_role("spinbutton")
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
    code_form = page.get_by_role("spinbutton").first.locator("xpath=ancestor::form")
    await code_form.get_by_role("button", name="NEXT").click()
    print("Clicked 'NEXT' on code form.")
    
    # Click 'MAYBE LATER' on the next screen
    print("Clicking 'MAYBE LATER'...")
    await page.get_by_role("button", name="MAYBE LATER").click()


async def perform_signup(page: Page) -> None:
    """
    Perform the complete sign-up process.
    
    Args:
        page: Playwright page object
    """
    print("Starting automated sign-up...")
    
    try:
        # Click join button
        await page.get_by_role("link", name="JOIN OkCupid").first.click()
        
        # Step 1: Basic info
        await fill_basic_info(page, config.SIGNUP_CONFIG)
        
        # Step 2: Location
        await fill_location(page, config.SIGNUP_CONFIG)
        
        # Step 3: Gender and preferences
        await fill_gender_and_preferences(page, config.SIGNUP_CONFIG)
        
        # Step 4: Date of birth
        await fill_date_of_birth(page, config.SIGNUP_CONFIG)
        
        # Step 5: Password
        await fill_password(page, config.SIGNUP_CONFIG)
        
        # Step 6: Dating goal and cookies
        await fill_dating_goal_and_handle_cookies(page, config.SIGNUP_CONFIG)
        
        # Step 7: Upload image
        await upload_profile_image(page, config.SIGNUP_CONFIG["profile_image_path"])
        await get_main_page_next_button(page).click()
        
        # Step 8: Self summary
        await fill_self_summary(page, config.SIGNUP_CONFIG)
        
        # Step 9: Answer questions
        await answer_profile_questions(page, config.QUESTIONS_CONFIG)
        
        # Step 10: Phone verification
        await handle_phone_verification(page, config.SMS_CONFIG)
        
        print("Sign-up complete!")
        
    except PWTimeoutError as e:
        print(f"Script timed out. An element was not found or page took too long: {e}")
        await page.screenshot(path=str(config.TIMEOUT_SCREENSHOT))
        print(f"Saved screenshot to {config.TIMEOUT_SCREENSHOT}")
        raise
    except Exception as e:
        print(f"An error occurred during sign-up: {e}")
        await page.screenshot(path=str(config.ERROR_SCREENSHOT))
        print(f"Saved screenshot to {config.ERROR_SCREENSHOT}")
        raise

