"""
Main entry point for OkCupid automation.
Supports both sign-up and login functionality.
"""

import sys
import asyncio
from okcupid_automation import OkCupidAutomation


def main():
    """Main function with CLI interface."""
    automation = OkCupidAutomation()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "signup":
            asyncio.run(automation.signup_flow())
        elif command == "login":
            asyncio.run(automation.login_flow())
        else:
            print(f"Unknown command: {command}")
            print("Usage: python main.py [signup|login]")
            sys.exit(1)
    else:
        print("No command specified. Running sign-up flow...")
        print("Usage: python main.py [signup|login]")
        print()
        asyncio.run(automation.signup_flow())


if __name__ == "__main__":
    main()
