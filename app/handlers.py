"""Command and message handlers for the bot."""

import asyncio
import logging
import re

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from app.models import get_chat_data
from app.services import (
    auto_process_delayed,
    clear_chat_data,
    format_timestamp,
    process_selected_messages,
    safe_delete_message,
)
from app.config import CATEGORIES

logger = logging.getLogger(__name__)


# Command handlers
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    await update.message.reply_text("Hello! I'm alive. Use /help for commands.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    await update.message.reply_text("Available commands: /start, /help, /process, /clear")


async def process_selected_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manual process command for immediate processing."""
    chat_id = update.effective_chat.id
    await process_selected_messages(chat_id, context)


async def clear_selected_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
            clean_content = text[match.end():].strip()
        else:
            # Invalid time, treat as regular '.' message
            timestamp = format_timestamp()
            clean_content = text[1:].strip()
    else:
        # Regular '.' message: use current time
        clean_content = text[1:].strip()
        timestamp = format_timestamp()

    # Apply category formatting: find first category occurring as a separate word prefix
    formatted_content = clean_content
    if CATEGORIES and formatted_content:
        # We consider category match at the start of content or after leading spaces
        # and followed by a space or end-of-string
        # Sort categories by length descending to prefer longest match first
        for category in sorted(CATEGORIES, key=len, reverse=True):
            # Build regex to match category as a whole word at start
            pattern = rf"^\s*({re.escape(category)})(?:\s+|$)"
            m = re.match(pattern, formatted_content, flags=re.IGNORECASE)
            if m:
                matched_cat = m.group(1)
                rest = formatted_content[m.end():].strip()
                if rest:
                    formatted_content = f"={matched_cat}= ({rest})"
                else:
                    # If no rest, still wrap the category and leave no parentheses
                    formatted_content = f"={matched_cat}="
                break
    
    message_data = {
        "message_id": update.message.message_id,
        "content": formatted_content,
        "timestamp": timestamp
    }
    
    data.selected_messages.append(message_data)
    
    # Auto-process after a delay to allow for multiple messages
    asyncio.create_task(auto_process_delayed(chat_id, context))


async def remove_service_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove service messages like pin/unpin notifications."""
    if update.message and update.message.from_user.is_bot:
        await safe_delete_message(
            context, 
            update.message.chat_id, 
            update.message.message_id
        )


async def handle_unpinned_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unpinned messages - clear processed data if our pinned message was unpinned."""
    if not update.message:
        return
    
    chat_id = update.effective_chat.id
    data = get_chat_data(chat_id)
    
    logger.info(f"Unpin event detected in chat {chat_id}, message_id: {update.message.message_id}, our pinned_id: {data.pinned_message_id}")
    
    # Check if the unpinned message was our pinned message
    if data.pinned_message_id and update.message.message_id == data.pinned_message_id:
        logger.info(f"Pinned message {data.pinned_message_id} was unpinned in chat {chat_id}")
        # Clear processed messages since the pinned message is gone
        data.clear_processed()
        data.clear_pinned()
        logger.info(f"Cleared processed messages for chat {chat_id} due to pinned message unpinning")
    else:
        logger.info(f"Unpinned message {update.message.message_id} was not our pinned message {data.pinned_message_id}")


def setup_handlers(application: Application) -> None:
    """Set up all message and command handlers."""
    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("process", process_selected_command))
    application.add_handler(CommandHandler("clear", clear_selected_command))

    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_message))
    application.add_handler(MessageHandler(filters.StatusUpdate.ALL, remove_service_messages))
    application.add_handler(MessageHandler(filters.StatusUpdate.UNPINNED_MESSAGE, handle_unpinned_message))

