"""
Telegram Document Module

This module defines the data model for Telegram messages stored in the database.
It includes fields for:
- Basic message information (channel, ID, timestamp, content)
- Metadata about the message
- Processing status flags
- Translation results
- Region information
"""

from beanie import Document, Indexed
from typing import Optional, List, Dict
from datetime import datetime


class TelegramMessage(Document):
    """
    Data model for Telegram messages.
    
    This class defines the structure of Telegram messages stored in the database.
    It includes fields for the message content, metadata, processing status,
    and translation results.
    """
    
    channel: str  # Channel the message was posted in
    message_id: Indexed(int)  # Message ID, indexed for faster queries
    timestamp: datetime  # When the message was posted
    content: str  # Raw message content
    metadata: Dict  # Additional metadata about the message
    media: List[Dict]  # Information about media attachments
    relevant_keywords: List[str] = []  # Keywords found in the message
    passed_keyword_filter: bool = False  # Whether the message passed keyword filtering
    passed_deduplication: bool = False  # Whether the message passed deduplication
    hebrew_translation: Optional[str] = None  # Hebrew translation of the message
    english_translation: Optional[str] = None  # English translation of the message
    region: str = (
        ""  # Track which region this message belongs to (hebron, etzion, etc.)
    )

    class Settings:
        name = "telegram_messages"  # Collection name in MongoDB

    class Config:
        schema_extra = {
            "example": {
                "channel": "example_channel",
                "message_id": 12345,
                "timestamp": "2024-10-21T12:34:56",
                "message": "Example message",
                "metadata": {
                    "sender_id": 67890,
                    "message_type": "Message",
                },
                "media": [],
                "relevant_keywords": [],
                "passed_keyword_filter": False,
                "passed_deduplication": False,
                "translation": None,
                "region": "hebron",
            }
        }
