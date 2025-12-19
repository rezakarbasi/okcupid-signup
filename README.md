# OkCupid Automation

A modular Python automation tool for OkCupid sign-up and login using Playwright with stealth mode. The tool automatically creates accounts, completes the sign-up process, and saves session state for easy future logins.

**⚠️ Important Notes:**
- This code **only supports sign-up and test of login** - nothing more
- The OkCupid UI changes frequently, so you may need to adapt the code after some time
- This code was working correctly **until December 2025**
- Phone verification uses **SMSPool** (https://smspool.net) for OTP/SMS codes

## Features

- ✅ **Automated Sign-up**: Complete OkCupid account creation with all required steps
- ✅ **Session Persistence**: Saves browser storage state (cookies, localStorage) for easy login
- ✅ **Stealth Mode**: Uses playwright-stealth to avoid detection
- ✅ **SMS Verification**: Integrated with SMSPool for phone number verification
- ✅ **Modular Design**: Clean, readable, and maintainable code structure
- ✅ **Configurable**: All settings in a single config file

## Project Structure

```
scrapprofile/
├── main.py              # Main entry point
├── config.py            # Configuration file (all static variables)
├── browser.py           # Browser setup and management
├── signup.py            # Sign-up automation logic
├── login.py             # Login using saved storage state
├── utils.py             # Utility functions
├── smspool_auto.py      # SMS verification service (SMSPool integration)
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── storage_state.json  # Saved session (created after sign-up)
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip

### Setup

1. **Clone or download this repository**

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers:**
   ```bash
   playwright install chromium
   ```

4. **Configure settings:**
   - Edit `config.py` to set your preferences (country, city, name, etc.)
   - Set `SMSPOOL_API_KEY` environment variable or edit it in `smspool_auto.py`
   - Ensure your profile image exists at the path specified in `config.py`

## Configuration

All configuration is done in `config.py`. Key settings include:

### Sign-up Configuration

```python
SIGNUP_CONFIG = {
    "email_base": "test.mail.okcupid",      # Base email string
    "first_name": "sarah",                # First name
    "country": "Finland",                 # Country name
    "country_code": "FI",                 # ISO country code
    "city": "Helsinki",                   # City name
    "gender": "Man",                      # Gender
    "interested_in": "Men",              # Dating preference
    "self_summary": "i am pretty girl love play",  # Bio text
    "profile_image_path": "personface.jpg",  # Profile image path
    # ... more settings
}
```

### SMS Configuration

**This code uses SMSPool (https://smspool.net) for phone number verification (OTP).**

You need to:
1. Sign up for a SMSPool account at https://smspool.net
2. Get your API key from your SMSPool dashboard
3. Set the `SMSPOOL_API_KEY` environment variable or edit `smspool_auto.py` directly

```python
SMS_CONFIG = {
    "country": "US",           # Country code for SMS service (ISO format)
    "service_id": 658,          # OkCupid service ID for SMSPool
    "api_key": None,            # Set via SMSPOOL_API_KEY env var or edit smspool_auto.py
}
```

### Browser Configuration

```python
HEADLESS = False               # Set to True for headless mode

# Proxy configuration (optional)
# Default: Uses socks5 proxy at 127.0.0.1:2070
# To disable proxy, set to None:
PROXY = None  # Disables proxy

# To use proxy, set to:
PROXY = {"server": "socks5://127.0.0.1:2070"}  # Default proxy
```

## Usage

### Sign-up (Create New Account)

Run the sign-up flow to create a new OkCupid account:

```bash
python main.py signup
```

This will:
1. Launch a browser with stealth mode
2. Navigate to OkCupid
3. Complete the entire sign-up process:
   - Enter email and name
   - Select country and city
   - Set gender and preferences
   - Enter date of birth (randomized)
   - Set password (randomly generated)
   - Upload profile image
   - Fill self-summary
   - Answer profile questions (randomly)
   - Verify phone number via SMS
4. Save storage state to `storage_state.json`

### Login (Use Saved Session)

After sign-up, you can log in using the saved session:

```bash
python main.py login
```

This will:
1. Load the saved storage state from `storage_state.json`
2. Launch browser with the saved session
3. Navigate to OkCupid (already logged in)
4. Keep browser open for interaction

## How It Works

### Sign-up Process

The sign-up process is broken down into modular steps:

1. **Basic Info**: Email (with random variations) and first name
2. **Location**: Country selection (with multiple fallback methods) and city
3. **Gender & Preferences**: Gender selection and dating preferences
4. **Date of Birth**: Random DOB within configured range
5. **Password**: Randomly generated secure password
6. **Dating Goal**: Select dating goal and handle cookie banner
7. **Profile Image**: Upload profile picture
8. **Self Summary**: Fill in bio text
9. **Profile Questions**: Answer questions randomly (configurable limit)
10. **Phone Verification**: Purchase phone number via SMSPool and verify SMS code

### Storage State

After successful sign-up, the browser's storage state (cookies, localStorage, sessionStorage) is saved to `storage_state.json`. This file contains all the authentication information needed to log in without going through the sign-up process again.

### SMS Verification (SMSPool)

**This tool uses SMSPool (https://smspool.net) for phone number verification (OTP).**

The integration works as follows:
- Purchases a phone number for the specified country via SMSPool API
- Waits for SMS code to arrive from OkCupid
- Automatically enters the verification code
- Handles resend requests if needed

**Requirements:**
- Active SMSPool account with sufficient balance
- Valid SMSPool API key (set via `SMSPOOL_API_KEY` environment variable)
- The service ID 658 must be available for your selected country

## Environment Variables

- `SMSPOOL_API_KEY`: Your SMSPool API key (required for SMS verification)

Set it before running:
```bash
export SMSPOOL_API_KEY="your_api_key_here"
```

Or edit `smspool_auto.py` directly.

## Troubleshooting

### Common Issues

1. **Storage file not found**
   - Run sign-up first: `python main.py signup`
   - Ensure `storage_state.json` exists in the project directory

2. **SMS verification fails**
   - Check your SMSPool API key
   - Verify you have sufficient balance in your SMSPool account
   - Check that the service ID (658) is available for your country

3. **Country dropdown not working**
   - The tool uses multiple fallback methods
   - Check `screenshots/country_dropdown_debug.png` if selection fails
   - Verify country name matches exactly as it appears in the dropdown

4. **Profile image not found**
   - Ensure the image file exists at the path specified in `config.py`
   - Use absolute path if relative path doesn't work

5. **Timeout errors**
   - Increase `BROWSER_TIMEOUT` in `config.py`
   - Check your internet connection
   - Verify proxy settings if using one

### Debug Mode

Set `HEADLESS = False` in `config.py` to see the browser in action. Screenshots are automatically saved to the `screenshots/` directory on errors.

## Code Structure

### Modular Design

The code is organized into logical modules:

- **`config.py`**: Centralized configuration
- **`browser.py`**: Browser lifecycle management
- **`signup.py`**: Sign-up automation (core logic)
- **`login.py`**: Login using saved state
- **`utils.py`**: Reusable utility functions
- **`main.py`**: Entry point and CLI

### Key Functions

- `perform_signup()`: Main sign-up orchestration
- `select_country_from_dropdown()`: Robust country selection with fallbacks
- `answer_profile_questions()`: Random question answering
- `handle_phone_verification()`: SMS verification flow

## Contributing

This is a modular codebase designed for easy maintenance and extension. To add new features:

1. Add configuration to `config.py`
2. Create utility functions in `utils.py` if needed
3. Extend sign-up steps in `signup.py`
4. Update this README

## License

This project is for educational purposes. Use responsibly and in accordance with OkCupid's Terms of Service.

## Important Limitations

⚠️ **This code has the following limitations:**

1. **Functionality**: This code **only supports sign-up and test of login** - it does not perform any other operations on OkCupid.

2. **UI Changes**: The OkCupid website UI changes frequently. This code was working correctly **until December 2025**. If the UI has changed since then, you will need to:
   - Update selectors in the code
   - Adjust wait times
   - Modify step sequences as needed
   - Check error screenshots for debugging

3. **SMSPool Dependency**: Phone verification requires an active SMSPool account and API key. Make sure you have sufficient balance and the service is available for your country.

4. **Maintenance**: This is a reference implementation. You are responsible for adapting it to current OkCupid UI changes.

## Disclaimer

This tool is provided as-is for educational and research purposes. Users are responsible for ensuring their use complies with OkCupid's Terms of Service and applicable laws.

**Last Known Working Date**: December 2025

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review error screenshots in `screenshots/` directory
3. Verify all configuration in `config.py`

---

**Note**: The most important part of this codebase is the sign-up automation in `signup.py`. The storage state file (`storage_state.json`) enables easy login after the initial sign-up process.

