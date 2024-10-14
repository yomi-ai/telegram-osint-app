import asyncio
from datetime import datetime, timedelta

import pytz
import json
from nest.core import Injectable
from pydantic.dataclasses import dataclass
from telethon import TelegramClient
from telethon.tl.patched import Message
from typing import IO

from src.providers.config.config_service import ConfigService
from src.providers.telegram.telegram_model import TelegramSettings
from src.providers.logger.logger_service import Logger

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
            self, channel_username: str, threshold_time: datetime
    ) -> list[dict]:
        """
        Reads messages from a specified Telegram channel within the given time interval.
        :param channel_username: Username of the channel to read messages from.
        :param threshold_time: The threshold time to filter messages after.
        :return: List of message objects in JSON format.
        """
        try:
            channel = await self._client.get_entity(channel_username)
            messages = await self._client.get_messages(channel, limit=100)

            # Filter messages after the threshold time
            filtered_messages = [
                m for m in messages if m.date and m.date >= threshold_time
            ]

            # Create a structured JSON result for each message
            result = []
            for message in filtered_messages:
                try:
                    ist_time = message.date.astimezone(ISRAEL_TZ)
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

    async def fetch_messages_from_channels(self):
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
        with open(f"{datetime.now()}/messages.json", 'w') as file:
            json.dumps(messages, file, indent=4)

        return messages

    async def telegram_fetch_and_send_job(self):
        """
        Fetches messages from multiple Telegram channels, translates them, and sends the important ones
        to a specific Telegram channel.
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

            # Assume a method `translate_and_filter_important_messages` to translate and filter messages.
            important_messages = self.translate_and_filter_important_messages(messages)

            # Send the important messages back to a specific channel.
            for important_message in important_messages:
                translated_message = (
                    important_message.message
                )  # Assuming this is the translated message
                await self.send_message_to_channel(
                    self.config_service, get("TARGET_CHANNEL"), translated_message
                )

        await self.disconnect()
        return messages

    def translate_and_filter_important_messages(
            self, messages: list[Message]
    ) -> list[Message]:
        """
        Filters and translates important messages. This is a placeholder function, and you should replace
        it with your actual translation and filtering logic.

        :param messages: The list of messages to process.
        :return: List of important messages.
        """
        # Placeholder: for now, we just return all messages as "important"
        # Implement your actual filtering and translation logic here.
        return messages

    async def disconnect(self):
        """
        Disconnects the Telegram client.
        """
        await self._client.disconnect()


if __name__ == "__main__":
    telegram_service = TelegramService()
    asyncio.run(telegram_service.fetch_messages_from_channels())
