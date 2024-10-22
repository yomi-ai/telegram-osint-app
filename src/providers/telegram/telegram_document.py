from beanie import Document, Indexed
from typing import Optional, List, Dict
from datetime import datetime


class TelegramMessage(Document):
    channel: str
    message_id: Indexed(int)  # Indexed for faster queries
    timestamp: datetime
    content: str
    metadata: Dict
    media: List[Dict]
    relevant_keywords: List[str] = []
    passed_keyword_filter: bool = False
    passed_deduplication: bool = False
    hebrew_translation: Optional[str] = None
    english_translation: Optional[str] = None

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
            }
        }
