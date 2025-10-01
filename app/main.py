"""FastAPI entry point that starts the Telegram bot on app startup."""

from a2wsgi import ASGIMiddleware
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from telegram.ext import Application

from app.config import BOT_TOKEN
from app.handlers import setup_handlers
from app.utils import setup_logging

logger = logging.getLogger(__name__)


telegram_application: Optional[Application] = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage the lifespan of the FastAPI application and Telegram bot."""
    global telegram_application

    # Startup
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

    yield

    # Shutdown
    if telegram_application is not None:
        logger.info("Stopping polling...")
        await telegram_application.updater.stop()
        logger.info("Stopping Telegram application...")
        await telegram_application.stop()
        logger.info("Shutting down Telegram application...")
        await telegram_application.shutdown()


app = FastAPI(title="Mukit Bot", version="1.0.0", lifespan=lifespan)


@app.get("/")
async def root() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.get("/healthz")
async def healthz() -> JSONResponse:
    is_bot_running = telegram_application is not None
    return JSONResponse({"status": "ok", "bot_running": is_bot_running})


application = ASGIMiddleware(app)
