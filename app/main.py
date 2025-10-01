"""FastAPI entry point that starts the Telegram bot on app startup."""

import logging
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


def initialize_bot() -> None:
    """Initialize the Telegram bot (called from WSGI level)."""
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


@app.get("/")
async def root() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.get("/healthz")
async def healthz() -> JSONResponse:
    is_bot_running = telegram_application is not None
    return JSONResponse({"status": "ok", "bot_running": is_bot_running})