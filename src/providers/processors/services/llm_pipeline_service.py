import json
from pathlib import Path

import pandas as pd
from nest.core import Injectable
from tqdm import tqdm

from src.providers.processors.services.ner_service import NERService
from src.providers.processors.services.translation_service import TranslationService
from src.providers.telegram.telegram_document import TelegramMessage
from src.providers.logger.logger_service import Logger


@Injectable()
class LLMPipelineService:
    ABS_PATH = Path(__file__).resolve().parent.parent.parent.parent

    def __init__(self, translator: TranslationService, ner_service: NERService, logger: Logger):
        self.translator = translator
        self.ner_service = ner_service
        self.logger = logger

    async def process_messages(self, messages: list[TelegramMessage]) -> list[TelegramMessage]:
        for msg in messages:
            try:
                if msg.passed_keyword_filter and msg.passed_deduplication is True:
                    # Perform translation
                    self.logger.info(f"Translating message - {msg.channel}:{msg.message_id}")
                    translation = self.translator.translate(msg.content)
                    msg.hebrew_translation = translation.hebrew
                    msg.english_translation = translation.english
                    # Update the message in MongoDB
                    await msg.save()
                    self.logger.info(f"Finish translating message {msg.channel}:{msg.message_id}")
            except Exception as e:
                self.logger.log.error(f"Error processing message: {e}")
                continue

        return messages
