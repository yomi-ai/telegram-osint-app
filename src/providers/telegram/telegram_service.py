import asyncio
from datetime import datetime, timedelta

import pytz
from nest.core import Injectable
from telethon import TelegramClient
from telethon.tl.patched import Message

from src.providers.config.config_service import ConfigService
from src.providers.telegram.telegram_model import TelegramSettings

CHANNELS = [
    "From_hebron",
    "HebMix",
    "hebron88",
    "HebronNewss",
    "abn_alkhalil",
    "khalelnews",
    "baninaem24",
    "baninaeim22"
]


@Injectable()
class TelegramService:
    def __init__(
            self,
            config_service: ConfigService,
            telegram_settings: TelegramSettings = TelegramSettings()):
        """
        Initializes the TelegramService with the provided Telegram settings.

        :param telegram_settings: Configuration settings for Telegram API access.
        """
        self.config_service = config_service
        self.telegram_settings = telegram_settings
        self._client = TelegramClient(
            self.telegram_settings.SESSION_NAME,
            self.config_service.get("API_ID"),
            self.config_service.get("API_HASH")
        )

    async def read_messages_from_channel(self, channel_username: str, limit: int = 100, interval: int = 5) -> list[
        Message]:
        """
        Reads messages from a specified Telegram channel within the given time interval.

        :param channel_username: Username of the channel to read messages from.
        :param limit: Number of messages to fetch from the channel.
        :param interval: Time interval in minutes to filter messages.
        :return: List of filtered message objects.
        """
        try:
            channel = await self._client.get_entity(channel_username)
            messages = await self._client.get_messages(channel, limit=limit)

            # Current UTC time
            current_time = datetime.utcnow().replace(tzinfo=pytz.UTC)
            # Threshold time
            threshold_time = current_time - timedelta(minutes=interval)

            # Filter messages within the last 'interval' minutes
            last_interval_messages = [
                m for m in messages if m.date and m.date >= threshold_time
            ]

            return last_interval_messages
        except Exception as e:
            # Log the exception (Assuming a logger is configured)
            print(f"Error reading messages from channel: {e}")
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
        for m in messages:
            print(m.message)
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
                translated_message = important_message.message  # Assuming this is the translated message
                await self.send_message_to_channel(self.config_service,get("TARGET_CHANNEL"), translated_message)

        await self.disconnect()
        return messages

    def translate_and_filter_important_messages(self, messages: list[Message]) -> list[Message]:
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


if __name__ == '__main__':
    telegram_service = TelegramService()
    asyncio.run(telegram_service.fetch_messages_from_channels())
