import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import IO

import pandas as pd
import pytz
from nest.core import Injectable
from pydantic.dataclasses import dataclass
from telethon import TelegramClient
from telethon.tl.patched import Message

from src.providers.config.config_service import ConfigService
from src.providers.logger.logger_service import Logger
from src.providers.telegram.telegram_model import TelegramSettings

CHANNELS = [
    "From_hebron",
    "HebMix",
    "hebron88",
    "HebronNewss",
    "abn_alkhalil",
    "khalelnews",
    "baninaem24",
    "baninaeim22",
]


@Injectable()
class TelegramService:
    ISRAEL_TZ = pytz.timezone("Asia/Jerusalem")
    ABS_PATH = Path(__file__).resolve().parent.parent.parent

    def __init__(
        self,
        config_service: ConfigService,
        logger: Logger,
        telegram_settings: TelegramSettings = TelegramSettings(),
    ):
        """
        Initializes the TelegramService with the provided Telegram settings.

        :param telegram_settings: Configuration settings for Telegram API access.
        """
        self.config_service = config_service
        self.telegram_settings = telegram_settings
        self.logger = logger
        self._client = TelegramClient(
            self.telegram_settings.SESSION_NAME,
            self.config_service.get("API_ID"),
            self.config_service.get("API_HASH"),
        )

    async def read_messages_from_channel(
        self, channel_username: str, limit: int = 100, interval: int = 5
    ) -> list[dict]:
        """
        Reads messages from a specified Telegram channel within the given time interval.

        :param channel_username: Username of the channel to read messages from.
        :param limit: Number of messages to fetch from the channel.
        :param interval: Time interval in minutes to filter messages.
        :return: List of filtered message objects.
        """
        try:
            result = []
            channel = await self._client.get_entity(channel_username)
            messages = await self._client.get_messages(channel, limit=limit)

            # Current UTC time
            current_time = datetime.utcnow().replace(tzinfo=pytz.UTC)
            # Threshold time
            threshold_time = current_time - timedelta(minutes=interval)

            # Filter messages after the threshold time
            filtered_messages = [
                m for m in messages if m.date and m.date >= threshold_time
            ]

            # Create a structured JSON result for each message
            for message in filtered_messages:
                try:
                    ist_time = message.date.astimezone(self.ISRAEL_TZ)
                    message_json = {
                        "channel": channel_username,
                        "message_id": message.id,
                        "timestamp": ist_time.strftime("%Y-%m-%d %H:%M:%S"),
                        "message": message.message or "",
                        "metadata": {
                            "sender_id": message.sender_id,
                            "message_type": type(message).__name__,
                        },
                        "media": [],
                    }

                    # Check if the message contains media
                    if message.media:
                        media_type = type(message.media).__name__
                        message_json["media"].append(
                            {"media_type": media_type, "media_id": message.id}
                        )

                    result.append(message_json)
                except Exception as e:
                    self.logger.log.debug(f"Error processing message: {e}")
                    continue
            return result
        except Exception as e:
            self.logger.log.error(
                f"Error reading messages from channel {channel_username}: {e}"
            )
            return []

    async def send_message_to_channel(self, channel_username: str, message_text: str):
        """
        Sends a message to a specific Telegram channel.

        :param channel_username: The username of the target channel.
        :param message_text: The message content to be sent.
        """
        try:
            channel = await self._client.get_entity(channel_username)
            await self._client.send_message(channel, message_text)
            print(f"Message sent to {channel_username}: {message_text}")
        except Exception as e:
            print(f"Error sending message to channel: {e}")

    async def fetch_messages_from_channels(self) -> pd.DataFrame:
        """
        Fetches messages from multiple Telegram channels and returns them.
        """
        messages: list[Message] = []
        await self._client.start()
        async with self._client:
            for channel in CHANNELS:
                messages += await self.read_messages_from_channel(
                    channel_username=channel,
                    limit=self.telegram_settings.FETCH_LIMIT,
                    interval=self.telegram_settings.MESSAGE_FILTER_INTERVAL_MINUTES,
                )

        await self.disconnect()

        # Audit the messages
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        audit_file_path = Path(f"{self.ABS_PATH}/data/{timestamp}/messages.json")
        audit_file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(audit_file_path, "w") as file:
            json.dump(messages, file, indent=4)

        return pd.json_normalize(messages)

    async def disconnect(self):
        """
        Disconnects the Telegram client.
        """
        await self._client.disconnect()
