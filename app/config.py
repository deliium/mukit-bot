"""Configuration constants and settings for the bot."""

import os
from typing import Final

try:
    # Load variables from a .env file if present
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    # If python-dotenv is not installed, fall back silently to environment only
    pass

# Bot configuration
BOT_TOKEN: Final[str] = os.getenv("BOT_TOKEN", "")

# Import categories from categories.py and flatten them
from app.categories import categories

# Flatten all categories into a single list, excluding 'Ушедшее'
CATEGORIES: Final[list[str]] = []
for category_name, subcategories in categories.items():
    CATEGORIES.extend(subcategories)

# Processing settings
AUTO_PROCESS_DELAY: Final[int] = 2  # seconds

# Logging configuration
LOG_FORMAT: Final[str] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL: Final[str] = "INFO"
