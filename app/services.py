"""Business logic and service functions for the bot."""

import asyncio
import logging
from datetime import datetime

from telegram.ext import ContextTypes

from app.config import AUTO_PROCESS_DELAY
from app.models import get_chat_data

logger = logging.getLogger(__name__)


def format_timestamp() -> str:
    """Get current timestamp in HH.MM format."""
    return datetime.now().strftime("%H.%M")


async def safe_delete_message(
    context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int
) -> bool:
    """Safely delete a message, return True if successful."""
    try:
        await context.bot.delete_message(chat_id, message_id)
        return True
    except Exception as e:
        logger.warning(f"Could not delete message {message_id}: {e}")
        return False


async def safe_edit_message(
    context: ContextTypes.DEFAULT_TYPE, chat_id: int, message_id: int, text: str
) -> bool:
    """Safely edit a message, return True if successful."""
    try:
        await context.bot.edit_message_text(
            chat_id=chat_id, message_id=message_id, text=text
        )
        return True
    except Exception as e:
        logger.warning(f"Could not edit message {message_id}: {e}")
        return False


async def create_new_pinned_message(
    chat_id: int, context: ContextTypes.DEFAULT_TYPE, summary_text: str
) -> None:
    """Create a new pinned message and track its ID."""
    try:
        summary_message = await context.bot.send_message(chat_id, summary_text)
        await context.bot.pin_chat_message(
            chat_id, summary_message.message_id, disable_notification=True
        )

        data = get_chat_data(chat_id)
        data.pinned_message_id = summary_message.message_id
    except Exception as e:
        logger.error(f"Error creating pinned message: {e}")


async def process_selected_messages(
    chat_id: int, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Process all selected messages and append to pinned message."""
    data = get_chat_data(chat_id)

    if not data.selected_messages:
        return

    try:
        # Check if our pinned message still exists before processing
        if data.pinned_message_id:
            try:
                # Check if there's still a pinned message in the chat
                chat_info = await context.bot.get_chat(chat_id)
                if (
                    not hasattr(chat_info, "pinned_message")
                    or chat_info.pinned_message is None
                ):
                    # No pinned message in chat, clear our data
                    data.clear_processed()
                    data.clear_pinned()
            except Exception:
                # Message doesn't exist or we can't access it, clear our data
                data.clear_processed()
                data.clear_pinned()

        # Add new messages to processed messages list
        for msg_data in data.selected_messages:
            new_message = {
                "timestamp": msg_data["timestamp"],
                "content": msg_data["content"]
            }
            
            # Check if this is a duplicate category (same category as the last message)
            if data.processed_messages:
                last_message = data.processed_messages[-1]
                # Extract category from last message (between = signs)
                last_content = last_message["content"]
                if last_content.startswith("=") and "=" in last_content[1:]:
                    last_category_end = last_content.find("=", 1)
                    last_category = last_content[1:last_category_end]
                    
                    # Extract category from new message
                    new_content = new_message["content"]
                    if new_content.startswith("=") and "=" in new_content[1:]:
                        new_category_end = new_content.find("=", 1)
                        new_category = new_content[1:new_category_end]
                        
                        # If same category, replace the last message instead of adding new one
                        if last_category.lower() == new_category.lower():
                            data.processed_messages[-1] = new_message
                            continue
            
            # If not a duplicate category, add as new message
            data.processed_messages.append(new_message)

        # Create the complete summary text with all processed messages
        summary_lines = [
            f"{msg['timestamp']} {msg['content']}" for msg in data.processed_messages
        ]

        if summary_lines:
            summary_text = "\n".join(summary_lines)

            # Update or create pinned message
            if data.pinned_message_id:
                success = await safe_edit_message(
                    context, chat_id, data.pinned_message_id, summary_text
                )
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


async def auto_process_delayed(
    chat_id: int, context: ContextTypes.DEFAULT_TYPE
) -> None:
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
            await context.bot.unpin_chat_message(
                chat_id, data.pinned_message_id, disable_notification=True
            )
            await safe_delete_message(context, chat_id, data.pinned_message_id)
            data.clear_pinned()
            cleared = True
        except Exception as e:
            logger.warning(f"Could not clear pinned message: {e}")

    return cleared
