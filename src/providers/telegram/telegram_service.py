import asyncio
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import IO
from tqdm import tqdm
import pandas as pd
import pytz
from nest.core import Injectable
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.patched import Message

from src.providers.config.config_service import ConfigService
from src.providers.logger.logger_service import Logger
from src.providers.telegram.telegram_model import TelegramSettings
from src.providers.processors.services.dedup_service import DeduplicationService

CHANNELS = [
    "From_hebron",
    "HebMix",
    "HebronNewss",
    "abn_alkhalil",
    "khalelnews",
    "baninaem24",
    "baninaeim22",
    "moltaqaidna0",
    "dahriyah3",
    "DuraCity",
    "doura2000",
    "z_0halhul",
    "halhul2024",
    "alsamou_alhadth",
    "Alsamo3News",
    "bietommar",
    "S3EERR",
    "saeare",
]

KEY_WORDS = [
    "الظاهرية",
    "دورا",
    "الخليل",
    "حلحول",
    "يطا",
    "مجالس محلية",
    "إذنا",
    "السموع",
    "بيت عوا",
    "بيت أولا",
    "بيت أمر",
    "بني نعيم",
    "دير سامت",
    "خاراس",
    "نوبا",
    "سعير",
    "صوريف",
    "تفوح",
    "ترقوميا",
    "الدوّارة",
    "الطبقة",
    "البقعة",
    "البرج",
    "الحيلة",
    "الكوم",
    "الكرمل",
    "قيلة",
    "أمريش",
    "الصورة",
    "الريحية",
    "الشيوخ",
    "بيت الروش الفوقا",
    "بيت كاحل",
    "بيت عمرة",
    "بيت عنون",
    "جبع",
    "دير العسل الفوقا",
    "زيف",
    "خلة المية",
    "حدب الفوار",
    "حوريس",
    "خربة السيميا",
    "خربة العدسية",
    "خربة كرمة",
    "خربة صفا",
    "خرسا",
    "كريسة الشرقية",
    "قلقاس",
    "رابود",
    "الرماضين",
    "شيوخ العروب",
    "العروب",
    "الفوار",
]


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

    # async def filter_relevant_messages(self, messages: list[Message], interval: int = 5) -> list[Message]:

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
            for message in tqdm(filtered_messages):
                try:
                    is_relevant_message = False
                    relevant_keyword = None

                    words = re.findall(r"\b\w+\b", message.message)

                    for keyword in KEY_WORDS:
                        if keyword in words:
                            is_relevant_message = True
                            relevant_keyword = keyword
                            break  # Exit the loop after finding a relevant keyword
                    if not is_relevant_message:
                        continue  # Skip to the next message if not relevant
                    print(
                        f"message-[{message.message}] | relevant_keyword=[{relevant_keyword}]"
                    )
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
                        "relevant_keywords": relevant_keyword or "",
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

    async def send_message_to_channel(self, message_text: str) -> bool:
        """
        Sends a message to a specific Telegram channel.

        :param channel_username: The username of the target channel.
        :param message_text: The message content to be sent.
        """
        try:
            await self._client.start()
            channel = await self._client.get_entity(self.target_channel)
            await self._client.send_message(channel, message_text)
            print(f"Message sent to {channel.title}: {message_text}")
            return True
        except Exception as e:
            print(f"Error sending message to channel: {e}")
            return False
        finally:
            await self.disconnect()

    async def fetch_messages_from_channels(self) -> pd.DataFrame:
        """
        Fetches messages from multiple Telegram channels and returns them.
        """
        messages: list[dict] = []
        await self._client.start()
        async with self._client:
            for channel in CHANNELS:
                channel_messages = await self.read_messages_from_channel(
                    channel_username=channel,
                    limit=self.telegram_settings.FETCH_LIMIT,
                    interval=self.telegram_settings.MESSAGE_FILTER_INTERVAL_MINUTES,
                )
                messages.extend(channel_messages)

        await self.disconnect()

        # remove dedup messages
        dedup_messages = self.dedup_service.deduplicate_messages(
            messages
        )

        # Audit the messages
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        audit_file_path = Path(f"{self.ABS_PATH}/data/{timestamp}/messages.json")
        audit_file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(audit_file_path, "w") as file:
            json.dump(dedup_messages, file, indent=4, ensure_ascii=False)

        return pd.json_normalize(dedup_messages)

    async def disconnect(self):
        """
        Disconnects the Telegram client.
        """
        await self._client.disconnect()
