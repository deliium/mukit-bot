import asyncio
import logging
import threading
from a2wsgi import ASGIMiddleware
from app.main import app, start_bot

logger = logging.getLogger(__name__)

# Global flag to track if bot is running
_bot_running = False
_bot_thread = None


def run_bot_in_thread():
    """Run the bot in a separate thread."""
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
    """Start the bot in a background thread."""
    global _bot_thread

    if _bot_thread is None or not _bot_thread.is_alive():
        _bot_thread = threading.Thread(target=run_bot_in_thread, daemon=True)
        _bot_thread.start()
        logger.info("Bot thread started")


def stop_bot_background():
    """Stop the bot background thread."""
    global _bot_running, _bot_thread

    if _bot_running and _bot_thread and _bot_thread.is_alive():
        # Signal the bot to stop
        _bot_running = False
        # The thread will exit when the event loop stops
        logger.info("Bot thread stop requested")


# Start the bot when the module is imported
start_bot_background()

# Create the WSGI application
application = ASGIMiddleware(app)
