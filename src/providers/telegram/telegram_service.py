import asyncio
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

import pytz
from beanie import PydanticObjectId
from nest.core import Injectable
from pyexpat.errors import messages
from telethon import TelegramClient, events
from telethon.events import NewMessage
from telethon.sessions import StringSession
from tqdm import tqdm

from src.mongo_config import config  # Import the ODM config
from src.providers.config.config_service import ConfigService
from src.providers.logger.logger_service import Logger
from src.providers.telegram.telegram_document import TelegramMessage
from src.providers.telegram.telegram_model import CHANNELS, KEY_WORDS, TelegramSettings


@Injectable()
class TelegramService:
    ISRAEL_TZ = pytz.timezone("Asia/Jerusalem")

    def __init__(
        self,
        config_service: ConfigService,
        logger: Logger,
    ):
        self.config_service = config_service
        self.target_channel = self.config_service.get("TARGET_CHANNEL")
        self.logger = logger

        session_string = self.config_service.get("SESSION_STRING")
        api_id = self.config_service.get("API_ID")
        api_hash = self.config_service.get("API_HASH")

        self._client = TelegramClient(StringSession(session_string), api_id, api_hash)

    @property
    def client(self) -> TelegramClient:
        """
        Provides access to the Telegram client for external usage.
        """
        return self._client

    async def process_new_message(self, event: NewMessage) -> TelegramMessage:
        """
        Processes a new message event.
        """
        message = event.message
        channel_id = event.chat_id
        channel_name = await self.client.get_entity(channel_id)

        self.logger.log.info(
            f"Received new message from channel: ** {channel_name.title} **"
        )

        # Create and save the message in MongoDB
        ist_time = message.date.astimezone(self.ISRAEL_TZ)
        telegram_message = TelegramMessage(
            channel=channel_name.username,
            message_id=message.id,
            timestamp=ist_time,
            content=message.message or "",
            metadata={
                "sender_id": message.sender_id,
                "message_type": type(message).__name__,
            },
            media=[],
        )

        # Check for media
        if message.media:
            media_type = type(message.media).__name__
            telegram_message.media.append(
                {"media_type": media_type, "media_id": message.id}
            )

        # Save to MongoDB
        await telegram_message.create()

        # Apply keyword filtering
        telegram_message = await self.apply_keyword_filter(telegram_message, KEY_WORDS)

        return telegram_message

    async def apply_keyword_filter(
        self, msg: TelegramMessage, keywords: List[str]
    ) -> TelegramMessage:
        """
        Filters messages by keywords, updates them in MongoDB with relevant flags.
        """
        self.logger.info(
            f"check if message {msg.message_id} from channel {msg.channel} contain relevant keywords"
        )

        words = re.findall(r"\b\w+\b", msg.content)

        for keyword in keywords:
            if keyword in words:
                msg.passed_keyword_filter = True
                msg.relevant_keywords = [keyword]
                break
                # Update the message in MongoDB
        await msg.save()

        self.logger.info(f"Finish filtering message by keywords")

        return msg

    async def send_message_to_channel(self, message_text: str) -> bool:
        try:
            channel = await self._client.get_entity(self.target_channel)
            await self._client.send_message(channel, message_text)
            self.logger.log.info(f"Message sent to {channel.title}: {message_text}")
            return True
        except Exception as e:
            self.logger.log.error(f"Error sending message to channel: {e}")
            return False
