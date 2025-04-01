"""
Telegram Service Module

This module provides functionality for interacting with Telegram channels, including:
- Fetching messages from specified channels
- Filtering messages based on keywords and exclusion criteria
- Deduplicating similar messages
- Sending processed messages to output channels

The service supports multiple regions (geographic areas) with different input/output
channels and filtering criteria for each region.
"""

from typing import List, Optional, Dict, Any
from beanie import PydanticObjectId
from nest.core import Injectable
from telethon import TelegramClient
from telethon.sessions import StringSession
import pytz
from datetime import datetime, timedelta
from tqdm import tqdm
import re
from pathlib import Path
import asyncio
from telethon.errors import RPCError
from telethon import events

from src.mongo_config import config  # Import the ODM config
from src.providers.telegram.telegram_document import TelegramMessage
from src.providers.config.config_service import ConfigService
from src.providers.logger.logger_service import Logger
from src.providers.telegram.telegram_model import (
    TelegramSettings,
    CHANNELS,
    KEY_WORDS,
    CHANNEL_CONFIGS,
)
from src.providers.processors.services.dedup_service import DeduplicationService


@Injectable()
class TelegramService:
    """
    Service for interacting with Telegram channels.
    
    This service handles all Telegram-related operations including:
    - Connecting to Telegram API
    - Reading messages from specified channels
    - Filtering messages based on keywords and exclusion criteria
    - Deduplicating similar messages
    - Sending processed messages to output channels
    
    The service uses a single Telegram client for all operations to avoid
    session-related issues when processing multiple regions.
    """
    
    ISRAEL_TZ = pytz.timezone("Asia/Jerusalem")
    ABS_PATH = Path(__file__).resolve().parent.parent.parent

    def __init__(
        self,
        config_service: ConfigService,
        logger: Logger,
        dedup_service: DeduplicationService,
        telegram_settings: TelegramSettings = TelegramSettings(),
    ):
        """
        Initialize the Telegram service.
        
        Args:
            config_service: Service for accessing configuration values
            logger: Service for logging
            dedup_service: Service for deduplicating messages
            telegram_settings: Settings for Telegram operations
        """
        self.config_service = config_service
        self.telegram_settings = telegram_settings
        self.target_channel = self.config_service.get("TARGET_CHANNEL")
        self.logger = logger
        self.channel_configs = CHANNEL_CONFIGS

        # Load the session string from a secure location or environment variable
        session_string = self.config_service.get("SESSION_STRING")
        api_id = self.config_service.get("API_ID")
        api_hash = self.config_service.get("API_HASH")

        # Create a single client for all operations with updates disabled
        self._client = TelegramClient(
            StringSession(session_string),
            api_id,
            api_hash,
            receive_updates=False  # Disable update handling
        )

        self.dedup_service = dedup_service

    async def _init_client(self):
        """Initialize the Telegram client with error handling for the update loop bug"""
        try:
            # Connect if not connected
            if not self._client.is_connected():
                await self._client.connect()
            
            # Add a custom error handler for the update loop
            @self._client.on(events.NewMessage)
            async def handle_update_error(event):
                try:
                    # Process the event normally
                    pass
                except RuntimeError as e:
                    if "Should not be applying the difference" in str(e):
                        self.logger.warning("Ignoring known Telethon v1.39.0 update loop bug")
                    else:
                        raise
        except Exception as e:
            self.logger.error(f"Error initializing Telegram client: {e}")

    async def read_messages_from_channel(
        self,
        channel_username: str,
        limit: int = 100,
        interval: int = 5,
        region: str = "default",
    ) -> List[TelegramMessage]:
        """
        Read messages from a specified Telegram channel within the given time interval.
        
        This method connects to a Telegram channel, retrieves recent messages,
        and saves them to the database with appropriate metadata.
        
        Args:
            channel_username: Username of the Telegram channel
            limit: Maximum number of messages to retrieve
            interval: Time interval in minutes to filter messages
            region: Region identifier for the channel
            
        Returns:
            List of TelegramMessage objects retrieved from the channel
        """
        try:
            self.logger.info(
                f"Start processing messages from - {channel_username} for region {region}"
            )
            result = []

            # Connect the client if not connected
            if not self._client.is_connected():
                await self._client.connect()

            channel = await self._client.get_entity(channel_username)
            messages = await self._client.get_messages(channel, limit=limit)

            current_time = datetime.utcnow().replace(tzinfo=pytz.UTC)
            threshold_time = current_time - timedelta(minutes=interval)

            filtered_messages = [
                m for m in messages if m.date and m.date >= threshold_time
            ]

            for message in filtered_messages:
                try:
                    ist_time = message.date.astimezone(self.ISRAEL_TZ)
                    if not message.message:
                        continue
                    telegram_message = TelegramMessage(
                        channel=channel_username,
                        message_id=message.id,
                        timestamp=ist_time,
                        content=message.message,
                        metadata={
                            "sender_id": message.sender_id,
                            "message_type": type(message).__name__,
                        },
                        media=[],
                        region=region,  # Set the region here
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
            self.logger.info(
                f"Finish processing messages from channel - {channel_username} for region {region}"
            )
            return result
        except Exception as e:
            self.logger.log.error(
                f"Error reading messages from channel {channel_username} for region {region}: {e}"
            )
            return []

    async def filter_messages_by_keywords(
        self,
        messages: List[TelegramMessage],
        keywords: List[str],
        exclude_words: List[str] = [],
    ) -> List[TelegramMessage]:
        """
        Filter messages based on keywords and exclusion criteria.
        
        This method:
        1. Checks if messages contain any exclusion words (if provided)
        2. Checks if messages contain any of the specified keywords
        3. Updates the messages in the database with filtering results
        
        Args:
            messages: List of messages to filter
            keywords: List of keywords to match
            exclude_words: List of words that should exclude a message if found
            
        Returns:
            Filtered list of TelegramMessage objects
        """
        self.logger.info(
            f"Start filtering messages by keywords. Number of initial messages - {len(messages)}"
        )
        filtered_messages = []

        for msg in messages:
            # First check for exclusion words
            should_exclude = False
            if exclude_words:
                for exclude_word in exclude_words:
                    if exclude_word in msg.content:
                        should_exclude = True
                        break

            if should_exclude:
                continue

            # Now check for relevant keywords
            is_relevant_message = False
            relevant_keywords = []

            words = re.findall(r"\b\w+\b", msg.content)

            for keyword in keywords:
                if keyword in words or keyword in msg.content:
                    is_relevant_message = True
                    relevant_keywords.append(keyword)

            if not is_relevant_message:
                continue  # Skip to the next message if not relevant

            msg.passed_keyword_filter = is_relevant_message
            msg.relevant_keywords = relevant_keywords

            # Update the message in MongoDB
            await msg.save()
            filtered_messages.append(msg)

        self.logger.info(
            f"Finish filtering messages by keywords. Number of final messages - {len(filtered_messages)}"
        )

        return filtered_messages

    async def deduplicate_messages(
        self, messages: List[TelegramMessage], similarity_threshold: float = 0.89
    ) -> List[TelegramMessage]:
        """
        Remove duplicate messages based on content similarity.
        
        This method uses the deduplication service to identify and remove
        messages that are too similar to each other.
        
        Args:
            messages: List of messages to deduplicate
            similarity_threshold: Threshold for considering messages as duplicates
            
        Returns:
            Deduplicated list of TelegramMessage objects
        """
        self.logger.info(f"Start with removing duplications - {len(messages)}")
        deduped_messages = self.dedup_service.deduplicate_messages(
            messages, similarity_threshold
        )
        deduped_ids = {msg.message_id for msg in deduped_messages}

        for msg in messages:
            msg.passed_deduplication = msg.message_id in deduped_ids
            # Update the message in MongoDB
            await msg.save()

        self.logger.info(
            f"Finish remove duplicate messages. Number of final messages - {len(deduped_messages)}"
        )

        return deduped_messages

    async def fetch_messages_from_channels(self) -> List[TelegramMessage]:
        """
        Fetch messages from multiple channels using the default Hebron configuration.
        
        This is a convenience method that calls fetch_messages_for_region with "hebron".
        
        Returns:
            Processed list of TelegramMessage objects
        """
        return await self.fetch_messages_for_region("hebron")

    async def fetch_messages_for_region(self, region: str) -> List[TelegramMessage]:
        """
        Fetch and process messages for a specific region.
        
        This method:
        1. Retrieves messages from all input channels for the specified region
        2. Filters messages based on region-specific keywords and exclusion criteria
        3. Deduplicates the filtered messages
        
        Args:
            region: Region identifier (e.g., "hebron", "etzion")
            
        Returns:
            Processed list of TelegramMessage objects for the region
        """
        if region not in self.channel_configs:
            self.logger.error(f"Unknown region: {region}")
            return []

        config = self.channel_configs[region]
        messages: List[TelegramMessage] = []

        # Get the client for this region
        client = self._client

        # Connect if not connected
        if not client.is_connected():
            await client.connect()

        # Fetch messages from all channels for this region
        for channel in config["input_channels"]:
            channel_messages = await self.read_messages_from_channel(
                channel_username=channel,
                limit=self.telegram_settings.FETCH_LIMIT,
                interval=self.telegram_settings.MESSAGE_FILTER_INTERVAL_MINUTES,
                region=region,  # Pass the region
            )
            messages.extend(channel_messages)

        # Filter messages by keywords and exclude words
        messages = await self.filter_messages_by_keywords(
            messages, config["keywords"], config["exclude_words"]
        )

        # Deduplicate messages
        messages = await self.deduplicate_messages(messages)

        return messages

    async def send_message_to_channel(self, message_text: str) -> bool:
        """
        Send a message to the default Hebron channel.
        
        This is a convenience method that calls send_message_to_region with "hebron".
        
        Args:
            message_text: Text of the message to send
            
        Returns:
            True if the message was sent successfully, False otherwise
        """
        return await self.send_message_to_region("hebron", message_text)

    async def send_message_to_region(self, region: str, message_text: str) -> bool:
        """
        Send a message to the specified region's output channel.
        
        Args:
            region: Region identifier (e.g., "hebron", "etzion")
            message_text: Text of the message to send
            
        Returns:
            True if the message was sent successfully, False otherwise
        """
        if region not in self.channel_configs:
            self.logger.error(f"Unknown region: {region}")
            return False

        output_channel_getter = self.channel_configs[region]["output_channel"]
        
        # Handle both direct strings and lambda functions
        if callable(output_channel_getter):
            output_channel = output_channel_getter()
        else:
            output_channel = output_channel_getter

        try:
            # Get the client for this region
            client = self._client

            # Connect if not connected
            if not client.is_connected():
                await client.connect()

            channel = await client.get_entity(output_channel)
            await client.send_message(channel, message_text)
            self.logger.log.info(f"Message sent to {region} channel")  # Don't log the actual channel
            return True
        except Exception as e:
            self.logger.log.error(f"Error sending message to {region} channel: {e}")
            return False

    async def disconnect_all(self):
        """
        Disconnect the Telegram client.
        
        This method should be called during application shutdown to properly
        close the Telegram connection.
        """
        if self._client.is_connected():
            self.logger.info("Disconnecting Telegram client")
            await self._client.disconnect()
