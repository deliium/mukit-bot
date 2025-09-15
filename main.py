"""FastAPI entry point that starts the Telegram bot on app startup."""

import logging
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from telegram.ext import Application

from config import BOT_TOKEN
from handlers import setup_handlers
from utils import setup_logging

logger = logging.getLogger(__name__)


app = FastAPI(title="Mukit Bot", version="1.0.0")

telegram_application: Optional[Application] = None


@app.on_event("startup")
async def on_startup() -> None:
    """Initialize logging and start the Telegram bot when the web app starts."""
    global telegram_application

    setup_logging()

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN environment variable is not set. Export BOT_TOKEN and retry."
        )

    telegram_application = Application.builder().token(BOT_TOKEN).build()
    setup_handlers(telegram_application)

    # Initialize and start bot without blocking the FastAPI event loop
    logger.info("Initializing Telegram application...")
    await telegram_application.initialize()
    logger.info("Starting Telegram application...")
    await telegram_application.start()
    logger.info("Starting polling...")
    await telegram_application.updater.start_polling()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """Gracefully stop the Telegram bot when the web app shuts down."""
    global telegram_application

    if telegram_application is None:
        return

    logger.info("Stopping polling...")
    await telegram_application.updater.stop()
    logger.info("Stopping Telegram application...")
    await telegram_application.stop()
    logger.info("Shutting down Telegram application...")
    await telegram_application.shutdown()


@app.get("/")
async def root() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.get("/healthz")
async def healthz() -> JSONResponse:
    is_bot_running = telegram_application is not None
    return JSONResponse({"status": "ok", "bot_running": is_bot_running})

    