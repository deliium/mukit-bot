"""Data models and structures for the bot."""

from typing import Dict, List, Optional


class ChatData:
    """Data structure to hold all chat-related information."""

    def __init__(self):
        self.selected_messages: List[Dict] = []
        self.processed_messages: List[Dict] = []
        self.pinned_message_id: Optional[int] = None

    def clear_selected(self) -> None:
        """Clear selected messages."""
        self.selected_messages.clear()

    def clear_processed(self) -> None:
        """Clear processed messages."""
        self.processed_messages.clear()

    def clear_pinned(self) -> None:
        """Clear pinned message ID."""
        self.pinned_message_id = None

    def clear_all(self) -> None:
        """Clear all data."""
        self.clear_selected()
        self.clear_processed()
        self.clear_pinned()


# Global storage: {chat_id: ChatData}
chat_data: Dict[int, ChatData] = {}


def get_chat_data(chat_id: int) -> ChatData:
    """Get or create chat data for the given chat ID."""
    if chat_id not in chat_data:
        chat_data[chat_id] = ChatData()
    return chat_data[chat_id]
