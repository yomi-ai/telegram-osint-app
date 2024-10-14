import asyncio

from nest.core import Injectable

from src.providers.logger.logger_service import Logger
from src.providers.openai.services.openai_service import OpenaiService
from src.providers.telegram.telegram_service import TelegramService


@Injectable()
class OsintJob:
    def __init__(
        self,
        telegram_service: TelegramService,
        openai_service: OpenaiService,
        logger_service: Logger,
    ):
        self.telegram_service = telegram_service
        self.openai_service = openai_service
        self.logger_service = logger_service

    async def run(self):
        while True:
            try:
                print("OsintJob started")
            except Exception as e:
                self.logger_service.log.error(e)
            finally:
                print("OsintJob finished")
                await asyncio.sleep(5 * 60)
