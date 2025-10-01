"""FastAPI entry point that starts the Telegram bot on app startup."""

import asyncio
import logging
import threading
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from telegram.ext import Application

from app.config import BOT_TOKEN
from app.handlers import setup_handlers
from app.utils import setup_logging

logger = logging.getLogger(__name__)

app = FastAPI(title="Mukit Bot", version="1.0.0")

telegram_application: Optional[Application] = None
_bot_running = False
_bot_thread = None


def initialize_bot() -> None:
    """Initialize the Telegram bot."""
    global telegram_application
    
    if telegram_application is not None:
        return  # Already initialized
    
    setup_logging()

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN environment variable is not set. Export BOT_TOKEN and retry."
        )

    telegram_application = Application.builder().token(BOT_TOKEN).build()
    setup_handlers(telegram_application)
    
    logger.info("Telegram application created and handlers set up")


async def start_bot() -> None:
    """Start the Telegram bot polling."""
    global telegram_application
    
    if telegram_application is None:
        initialize_bot()
    
    if telegram_application is not None:
        logger.info("Initializing Telegram application...")
        await telegram_application.initialize()
        logger.info("Starting Telegram application...")
        await telegram_application.start()
        logger.info("Starting polling...")
        await telegram_application.updater.start_polling()


async def stop_bot() -> None:
    """Stop the Telegram bot."""
    global telegram_application
    
    if telegram_application is not None:
        logger.info("Stopping polling...")
        await telegram_application.updater.stop()
        logger.info("Stopping Telegram application...")
        await telegram_application.stop()
        logger.info("Shutting down Telegram application...")
        await telegram_application.shutdown()
        telegram_application = None


def run_bot_in_thread():
    """Run the bot in a separate thread for local development."""
    global _bot_running
    
    try:
        _bot_running = True
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Start the bot
        loop.run_until_complete(start_bot())
        
        # Keep the loop running
        loop.run_forever()
    except Exception as e:
        logger.error(f"Error in bot thread: {e}")
    finally:
        _bot_running = False


def start_bot_background():
    """Start the bot in a background thread for local development."""
    global _bot_thread
    
    if _bot_thread is None or not _bot_thread.is_alive():
        _bot_thread = threading.Thread(target=run_bot_in_thread, daemon=True)
        _bot_thread.start()
        logger.info("Bot thread started for local development")


# Start the bot when running locally with uvicorn
if __name__ != "__main__":
    # This runs when imported (like with uvicorn)
    start_bot_background()


@app.get("/")
async def root() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.get("/healthz")
async def healthz() -> JSONResponse:
    is_bot_running = telegram_application is not None
    return JSONResponse({"status": "ok", "bot_running": is_bot_running})