"""Business logic and service functions for the bot."""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from telegram.ext import ContextTypes

from app.config import AUTO_PROCESS_DELAY
from app.models import get_chat_data

logger = logging.getLogger(__name__)


def format_timestamp() -> str:
    """Get current timestamp in HH.MM format."""
    return datetime.now().strftime("%H.%M")


async def safe_delete_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int) -> bool:
    """Safely delete a message, return True if successful."""
    try:
        await context.bot.delete_message(chat_id, message_id)
        return True
    except Exception as e:
        logger.warning(f"Could not delete message {message_id}: {e}")
        return False


async def safe_edit_message(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int, text: str) -> bool:
    """Safely edit a message, return True if successful."""
    try:
        await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text)
        return True
    except Exception as e:
        logger.warning(f"Could not edit message {message_id}: {e}")
        return False


async def create_new_pinned_message(chat_id: int, context: ContextTypes.DEFAULT_TYPE, summary_text: str) -> None:
    """Create a new pinned message and track its ID."""
    try:
        summary_message = await context.bot.send_message(chat_id, summary_text)
        await context.bot.pin_chat_message(chat_id, summary_message.message_id, disable_notification=True)

        data = get_chat_data(chat_id)
        data.pinned_message_id = summary_message.message_id
    except Exception as e:
        logger.error(f"Error creating pinned message: {e}")


async def process_selected_messages(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process all selected messages and append to pinned message."""
    data = get_chat_data(chat_id)

    if not data.selected_messages:
        return

    try:
        # Add new messages to processed messages list
        for msg_data in data.selected_messages:
            data.processed_messages.append({
                "timestamp": msg_data["timestamp"],
                "content": msg_data["content"]
            })

        # Create the complete summary text with all processed messages
        summary_lines = [
            f"{msg['timestamp']} {msg['content']}"
            for msg in data.processed_messages
        ]

        if summary_lines:
            summary_text = "\n".join(summary_lines)

            # Update or create pinned message
            if data.pinned_message_id:
                success = await safe_edit_message(context, chat_id, data.pinned_message_id, summary_text)
                if not success:
                    await create_new_pinned_message(chat_id, context, summary_text)
            else:
                await create_new_pinned_message(chat_id, context, summary_text)

            # Delete all selected messages
            for msg_data in data.selected_messages:
                await safe_delete_message(context, chat_id, msg_data["message_id"])

            # Clear the selected messages
            data.selected_messages.clear()

    except Exception as e:
        logger.error(f"Error processing selected messages: {e}")


async def auto_process_delayed(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Auto-process selected messages after a delay."""
    await asyncio.sleep(AUTO_PROCESS_DELAY)
    await process_selected_messages(chat_id, context)


async def clear_chat_data(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Clear all chat data and pinned message. Returns True if anything was cleared."""
    data = get_chat_data(chat_id)
    cleared = False

    # Clear selected messages
    if data.selected_messages:
        data.clear_selected()
        cleared = True

    # Clear processed messages
    if data.processed_messages:
        data.clear_processed()
        cleared = True

    # Clear pinned message
    if data.pinned_message_id:
        try:
            await context.bot.unpin_chat_message(chat_id, data.pinned_message_id, disable_notification=True)
            await safe_delete_message(context, chat_id, data.pinned_message_id)
            data.clear_pinned()
            cleared = True
        except Exception as e:
            logger.warning(f"Could not clear pinned message: {e}")

    return cleared

