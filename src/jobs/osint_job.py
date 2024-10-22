# src/jobs/osint_job.py

from nest.core import Injectable
from src.providers.logger.logger_service import Logger
from src.providers.telegram.telegram_service import TelegramService
from src.providers.processors.services.llm_pipeline_service import LLMPipelineService
from src.providers.telegram.telegram_document import TelegramMessage

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
                telegram_messages = await self.telegram_service.fetch_messages_from_channels()
                # Process messages through LLM pipeline
                processed_messages = await self.llm_pipeline_service.process_messages(telegram_messages)

                for msg in processed_messages:
                    if msg.translation:
                        message_to_send = msg.translation
                        message_to_send += f"\nhttps://t.me/{msg.channel}/{msg.message_id}"
                        await self.telegram_service.send_message_to_channel(message_to_send)
                        await asyncio.sleep(5)
            except Exception as e:
                self.logger_service.log.error(e)
            finally:
                print("OsintJob finished")
                await asyncio.sleep(10 * 60)
