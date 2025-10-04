"""Command and message handlers for the bot."""

import asyncio
import logging
import re

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.models import get_chat_data
from app.services import (
    auto_process_delayed,
    clear_chat_data,
    format_timestamp,
    process_selected_messages,
    safe_delete_message,
    safe_edit_message,
    create_new_pinned_message,
)
from app.config import CATEGORIES

logger = logging.getLogger(__name__)


# Command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    await update.message.reply_text("Hello! I'm alive. Use /help for commands.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    await update.message.reply_text(
        "Available commands: /start, /help, /process, /clear"
    )


async def process_selected_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Manual process command for immediate processing."""
    chat_id = update.effective_chat.id
    await process_selected_messages(chat_id, context)


async def clear_selected_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Clear all selected messages, processed messages, and pinned message for the current chat."""
    chat_id = update.effective_chat.id
    cleared = await clear_chat_data(chat_id, context)
    await update.message.reply_text("Cleared." if cleared else "Nothing to clear.")


# Message handlers
async def echo_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle text messages that start with '.'."""
    if not update.message or not update.message.text:
        return

    text = update.message.text
    if not text.startswith("."):
        return

    chat_id = update.effective_chat.id
    data = get_chat_data(chat_id)

    # Handle special ".-" command to remove last message
    if text == ".-":
        await remove_last_message(chat_id, context)
        # Delete the command message itself
        await safe_delete_message(context, chat_id, update.message.message_id)
        return

    # Extract and store the message data
    # Support prefixes ".H.MM" or ".HH.MM" to override timestamp
    time_prefix_regex = r"^\.(\d{1,2})\.(\d{2})(?:\s+|$)"
    match = re.match(time_prefix_regex, text)
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2))
        if 0 <= hours <= 23 and 0 <= minutes <= 59:
            timestamp = f"{hours:02d}.{minutes:02d}"
            # Remaining content after the matched time prefix
            clean_content = text[match.end() :].strip()
        else:
            # Invalid time, treat as regular '.' message
            timestamp = format_timestamp()
            clean_content = text[1:].strip()
    else:
        # Regular '.' message: use message timestamp from Telegram
        clean_content = text[1:].strip()
        # Use the actual message time from Telegram as shown in chat
        message_time = update.message.date

        # Telegram message.date is UTC, but we want the time as it appears in the user's chat
        # Convert UTC to the user's local timezone (same timezone as the chat interface)
        try:
            # Convert UTC to local timezone
            local_time = message_time.astimezone()
            timestamp = local_time.strftime("%H.%M")
        except Exception:
            # Fallback to current time if conversion fails
            timestamp = format_timestamp()

    # Normalize content: lowercase first letter if it exists
    if clean_content and clean_content[0].isupper():
        clean_content = clean_content[0].lower() + clean_content[1:]

    # Apply category formatting: find first category occurring as a separate word prefix
    formatted_content = clean_content
    if CATEGORIES and formatted_content:
        # Sort categories by length descending to prefer longest match first
        for category in sorted(CATEGORIES, key=len, reverse=True):
            # Check if content starts with the category (case-insensitive)
            if formatted_content.lower().startswith(category.lower()):
                # Check if it's followed by space or end of string
                if (
                    len(formatted_content) == len(category)
                    or formatted_content[len(category)] == " "
                ):
                    matched_cat = formatted_content[: len(category)]
                    rest = formatted_content[len(category) :].strip()
                    if rest:
                        formatted_content = f"={matched_cat}= ({rest})"
                    else:
                        # If no rest, still wrap the category and leave no parentheses
                        formatted_content = f"={matched_cat}="
                    break

    message_data = {
        "message_id": update.message.message_id,
        "content": formatted_content,
        "timestamp": timestamp,
    }

    data.selected_messages.append(message_data)

    # Auto-process after a delay to allow for multiple messages
    asyncio.create_task(auto_process_delayed(chat_id, context))


async def remove_last_message(chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove the last message from processed messages and update pinned message."""
    data = get_chat_data(chat_id)

    if not data.processed_messages:
        # No messages to remove
        return

    # Remove the last processed message
    data.processed_messages.pop()

    # Update the pinned message with remaining messages
    if data.processed_messages:
        # Create the updated summary text
        summary_lines = [
            f"{msg['timestamp']} {msg['content']}" for msg in data.processed_messages
        ]
        summary_text = "\n".join(summary_lines)

        # Update or create pinned message
        if data.pinned_message_id:
            success = await safe_edit_message(
                context, chat_id, data.pinned_message_id, summary_text
            )
            if not success:
                # If edit failed, create new pinned message
                await create_new_pinned_message(chat_id, context, summary_text)
        else:
            await create_new_pinned_message(chat_id, context, summary_text)
    else:
        # No more messages, clear the pinned message
        if data.pinned_message_id:
            try:
                await context.bot.unpin_chat_message(chat_id, data.pinned_message_id)
                await safe_delete_message(context, chat_id, data.pinned_message_id)
                data.clear_pinned()
            except Exception as e:
                logger.warning(f"Could not clear pinned message: {e}")


async def remove_service_messages(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Remove service messages like pin/unpin notifications."""
    if update.message and update.message.from_user.is_bot:
        await safe_delete_message(
            context, update.message.chat_id, update.message.message_id
        )


def setup_handlers(application: Application) -> None:
    """Set up all message and command handlers."""
    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("process", process_selected_command))
    application.add_handler(CommandHandler("clear", clear_selected_command))

    # Message handlers
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, echo_message)
    )
    application.add_handler(
        MessageHandler(filters.StatusUpdate.ALL, remove_service_messages)
    )
