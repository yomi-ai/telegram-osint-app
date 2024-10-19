import asyncio

from nest.core import Injectable

from src.providers.logger.logger_service import Logger
from src.providers.openai.services.openai_service import OpenAIClientService
from src.providers.processors.services.llm_pipeline_service import LLMPipelineService
from src.providers.telegram.telegram_service import TelegramService
from src.taskqueue.faust import parse_messages

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
                print("Sending messages to the queue...")
                failed_messages = await parse_messages.ask(telegram_messages)
                if len(failed_messages) > 0:
                    raise Exception("Failed to deliver these telegram messages to the target channel:\n" + "\n".join(failed_messages))
                else:
                    print("Messages successfully parsed!")
            except Exception as e:
                self.logger_service.log.error(e)
            finally:
                print("OsintJob finished")
                await asyncio.sleep(10 * 60)
