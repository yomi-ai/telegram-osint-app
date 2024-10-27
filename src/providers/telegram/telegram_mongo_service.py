from datetime import datetime

from nest.core import Injectable

from src.providers.telegram.telegram_document import TelegramMessage


@Injectable()
class TelegramMongoService:

    @staticmethod
    async def get_all_messages(limit: int = 100):
        messages = await TelegramMessage.find_all(limit=limit).to_list()
        return messages

    @staticmethod
    async def get_messages_with_hebrew_translation(
        since_timestamp: datetime,
    ) -> list[TelegramMessage]:
        messages = await TelegramMessage.find(
            TelegramMessage.hebrew_translation != None,
            TelegramMessage.hebrew_translation != "",
            TelegramMessage.timestamp > since_timestamp,
        ).to_list()
        return messages
