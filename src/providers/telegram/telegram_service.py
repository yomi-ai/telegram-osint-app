from typing import List
from beanie import PydanticObjectId
from nest.core import Injectable
from telethon import TelegramClient
from telethon.sessions import StringSession
import pytz
from datetime import datetime, timedelta
from tqdm import tqdm
import re
from pathlib import Path


from src.mongo_config import config  # Import the ODM config
from src.providers.telegram.telegram_document import TelegramMessage
from src.providers.config.config_service import ConfigService
from src.providers.logger.logger_service import Logger
from src.providers.telegram.telegram_model import TelegramSettings, CHANNELS, KEY_WORDS
from src.providers.processors.services.dedup_service import DeduplicationService

@Injectable()
class TelegramService:
    ISRAEL_TZ = pytz.timezone("Asia/Jerusalem")
    ABS_PATH = Path(__file__).resolve().parent.parent.parent

    def __init__(
        self,
        config_service: ConfigService,
        logger: Logger,
        dedup_service: DeduplicationService,
        telegram_settings: TelegramSettings = TelegramSettings(),
    ):
        self.config_service = config_service
        self.telegram_settings = telegram_settings
        self.target_channel = self.config_service.get("TARGET_CHANNEL")
        self.logger = logger

        # Load the session string from a secure location or environment variable
        session_string = self.config_service.get("SESSION_STRING")
        api_id = self.config_service.get("API_ID")
        api_hash = self.config_service.get("API_HASH")

        self._client = TelegramClient(
            StringSession(session_string),
            api_id,
            api_hash,
        )
        self.dedup_service = dedup_service

    async def read_messages_from_channel(
        self, channel_username: str, limit: int = 100, interval: int = 5
    ) -> List[TelegramMessage]:
        """
        Reads messages from a specified Telegram channel within the given time interval.
        Saves the raw messages to MongoDB.
        """
        try:
            result = []
            channel = await self._client.get_entity(channel_username)
            messages = await self._client.get_messages(channel, limit=limit)

            current_time = datetime.utcnow().replace(tzinfo=pytz.UTC)
            threshold_time = current_time - timedelta(minutes=interval)

            filtered_messages = [m for m in messages if m.date and m.date >= threshold_time]

            for message in filtered_messages:
                try:
                    ist_time = message.date.astimezone(self.ISRAEL_TZ)
                    telegram_message = TelegramMessage(
                        channel=channel_username,
                        message_id=message.id,
                        timestamp=ist_time,
                        content=message.message or "",
                        metadata={
                            "sender_id": message.sender_id,
                            "message_type": type(message).__name__,
                        },
                        media=[],
                    )

                    # Check for media attachments
                    if message.media:
                        media_type = type(message.media).__name__
                        telegram_message.media.append(
                            {"media_type": media_type, "media_id": message.id}
                        )

                    # Save the raw message to MongoDB
                    await telegram_message.create()

                    result.append(telegram_message)
                except Exception as e:
                    self.logger.log.debug(f"Error processing message: {e}")
                    continue
            return result
        except Exception as e:
            self.logger.log.error(
                f"Error reading messages from channel {channel_username}: {e}"
            )
            return []

    async def filter_messages_by_keywords(
        self, messages: List[TelegramMessage], keywords: List[str]
    ) -> List[TelegramMessage]:
        """
        Filters messages by keywords, updates them in MongoDB with relevant flags.
        """
        for msg in messages:
            is_relevant_message = False
            relevant_keyword = None

            words = re.findall(r"\b\w+\b", msg.content)

            for keyword in KEY_WORDS:
                if keyword in words:
                    is_relevant_message = True
                    relevant_keyword = keyword
                    break  # Exit the loop after finding a relevant keyword
            if not is_relevant_message:
                continue  # Skip to the next message if not relevant

            msg.passed_keyword_filter = is_relevant_message
            msg.relevant_keywords = [relevant_keyword]

            # Update the message in MongoDB
            await msg.save()

        return messages

    async def deduplicate_messages(
        self, messages: List[TelegramMessage], similarity_threshold: float = 0.89
    ) -> List[TelegramMessage]:
        """
        Removes duplicates from the messages, updates them in MongoDB.
        """
        deduped_messages = self.dedup_service.deduplicate_messages(
            messages, similarity_threshold
        )
        deduped_ids = {msg.message_id for msg in deduped_messages}

        for msg in messages:
            msg.passed_deduplication = msg.message_id in deduped_ids
            # Update the message in MongoDB
            await msg.save()

        return messages

    async def fetch_messages_from_channels(self) -> List[TelegramMessage]:
        """
        Fetches messages from multiple channels, processes them (filters and deduplicates),
        and returns the processed list of messages.
        """
        messages: List[TelegramMessage] = []
        async with self._client:
            for channel in CHANNELS:
                channel_messages = await self.read_messages_from_channel(
                    channel_username=channel,
                    limit=self.telegram_settings.FETCH_LIMIT,
                    interval=self.telegram_settings.MESSAGE_FILTER_INTERVAL_MINUTES,
                )
                messages.extend(channel_messages)

        # Filter messages by keywords
        messages = await self.filter_messages_by_keywords(messages, KEY_WORDS)

        # Deduplicate messages
        messages = await self.deduplicate_messages(messages)

        return messages

    async def send_message_to_channel(self, message_text: str) -> bool:
        """
        Sends a message to the specified Telegram channel.
        """
        try:
            async with self._client:
                channel = await self._client.get_entity(self.target_channel)
                await self._client.send_message(channel, message_text)
                self.logger.log.info(f"Message sent to {channel.title}: {message_text}")
            return True
        except Exception as e:
            print(f"Error sending message to channel: {e}")
            return False

    async def disconnect(self):
        """
        Disconnects the Telegram client.
        """
        await self._client.disconnect()
