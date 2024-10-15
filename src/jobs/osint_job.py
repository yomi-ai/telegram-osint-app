import asyncio

from nest.core import Injectable

from src.providers.logger.logger_service import Logger
from src.providers.openai.services.openai_service import OpenAIClientService
from src.providers.processors.services.llm_pipeline_service import LLMPipelineService
from src.providers.telegram.telegram_service import TelegramService


@Injectable()
class OsintJob:
    def __init__(
        self,
        telegram_service: TelegramService,
        llm_pipeline_service: LLMPipelineService,
        logger_service: Logger,
    ):
        self.telegram_service = telegram_service
        self.llm_pipeline_service = llm_pipeline_service
        self.logger_service = logger_service

    async def run(self):
        while True:
            try:
                telegram_messages = (
                    await self.telegram_service.fetch_messages_from_channels()
                )
                df = self.llm_pipeline_service.process_dataframe(telegram_messages)

            except Exception as e:
                self.logger_service.log.error(e)
            finally:
                print("OsintJob finished")
                await asyncio.sleep(5 * 60)
