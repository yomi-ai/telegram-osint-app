import asyncio

from nest.core import Injectable

from src.providers.healthchecks.healthchecks_service import HealthchecksService
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
        healthchecks_service: HealthchecksService,
    ):
        self.telegram_service = telegram_service
        self.llm_pipeline_service = llm_pipeline_service
        self.logger_service = logger_service
        self.healthchecks_service = healthchecks_service

    async def run(self):
        while True:
            await self.healthchecks_service.healthchecks_signal_start()
            try:
                telegram_messages = (
                    await self.telegram_service.fetch_messages_from_channels()
                )
                df = self.llm_pipeline_service.process_dataframe(telegram_messages)
                for index, row in df.iterrows():
                    try:
                        message_to_send = row["hebrew_translation"]
                        message_to_send += f"\nhttps://t.me/{row['channel']}/{row['message_id']}"
                        await self.telegram_service.send_message_to_channel(message_to_send)
                        await asyncio.sleep(1)
                    except Exception as e:
                        self.logger_service.log.error(e)
                        continue
                await self.healthchecks_service.healthchecks_signal_success()
            except Exception as e:
                self.logger_service.log.error(e)
                await self.healthchecks_service.healthchecks_signal_fail()
            finally:
                print("OsintJob finished")
                await asyncio.sleep(10 * 60)
