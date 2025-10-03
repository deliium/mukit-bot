#!/usr/bin/env python3
"""Standalone bot runner that runs independently of the web server."""

import asyncio
import json
import logging
import os
import signal
import sys
from pathlib import Path

from telegram.ext import Application

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.config import BOT_TOKEN
from app.handlers import setup_handlers
from app.utils import setup_logging

logger = logging.getLogger(__name__)

# Status file for communication with FastAPI
STATUS_FILE = Path("/tmp/mukit_bot_status.json")
PID_FILE = Path("/tmp/mukit_bot.pid")


def write_status(status: str, error: str = None) -> None:
    """Write bot status to a file for FastAPI to read."""
    try:
        status_data = {
            "status": status,
            "error": error,
            "timestamp": asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else 0
        }
        with open(STATUS_FILE, "w") as f:
            json.dump(status_data, f)
    except Exception as e:
        logger.error(f"Failed to write status: {e}")


async def main() -> None:
    """Main function to run the bot."""
    setup_logging()
    write_status("starting")
    
    if not BOT_TOKEN:
        error_msg = "BOT_TOKEN environment variable is not set"
        logger.error(error_msg)
        write_status("error", error_msg)
        return

    try:
        # Create application
        application = Application.builder().token(BOT_TOKEN).build()
        setup_handlers(application)
        
        write_status("initializing")
        logger.info("Initializing Telegram application...")
        await application.initialize()
        
        write_status("starting")
        logger.info("Starting Telegram application...")
        await application.start()
        
        write_status("running")
        logger.info("Starting polling...")
        await application.updater.start_polling()
        
        logger.info("Bot is running and polling for updates...")
        
        # Keep the bot running
        while True:
            await asyncio.sleep(1)
            
    except Exception as e:
        error_msg = f"Bot error: {e}"
        logger.error(error_msg)
        write_status("error", error_msg)
        raise
    finally:
        write_status("stopping")
        try:
            if 'application' in locals():
                logger.info("Stopping polling...")
                await application.updater.stop()
                logger.info("Stopping Telegram application...")
                await application.stop()
                logger.info("Shutting down Telegram application...")
                await application.shutdown()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        write_status("stopped")


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, shutting down...")
    write_status("stopping")
    # Remove PID file
    try:
        if PID_FILE.exists():
            PID_FILE.unlink()
    except Exception:
        pass
    sys.exit(0)


if __name__ == "__main__":
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        write_status("error", str(e))
        sys.exit(1)
