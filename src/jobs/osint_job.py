import asyncio


from nest.core import Injectable
from src.providers.logger.logger_service import Logger
from src.providers.telegram.telegram_service import TelegramService
from src.providers.processors.services.llm_pipeline_service import LLMPipelineService
from src.providers.telegram.telegram_document import TelegramMessage
from src.providers.healthchecks.healthchecks_service import HealthchecksService


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
        self.regions = ["hebron", "etzion"]

    async def process_region(self, region: str):
        """Process messages for a specific region"""
        try:
            self.logger_service.info(f"Processing region: {region}")
            # Retrieve messages from telegram for this region
            telegram_messages = await self.telegram_service.fetch_messages_for_region(
                region
            )

            # Process messages through LLM pipeline
            processed_messages = await self.llm_pipeline_service.process_messages(
                telegram_messages
            )

            # Send messages to the appropriate channel
            try:
                for msg in processed_messages:
                    if msg.hebrew_translation:
                        message_to_send = msg.hebrew_translation
                        message_to_send += (
                            f"\nhttps://t.me/{msg.channel}/{msg.message_id}"
                        )
                        self.logger_service.info(
                            f"Sending message to {region} channel - message: \n{message_to_send}\n"
                        )
                        await self.telegram_service.send_message_to_region(
                            region, message_to_send
                        )
                        await asyncio.sleep(5)
            except Exception as e:
                self.logger_service.error(
                    f"Failed to send message for {region} due to {e}"
                )

            return True
        except Exception as e:
            self.logger_service.error(f"Error processing region {region}: {e}")
            return False

    async def run(self):
        while True:
            await self.healthchecks_service.healthchecks_signal_start()
            success = True

            try:
                self.logger_service.info("Starting OSINTJob!")

                # Process each region
                for region in self.regions:
                    region_success = await self.process_region(region)
                    if not region_success:
                        success = False

                if success:
                    await self.healthchecks_service.healthchecks_signal_success()
                else:
                    await self.healthchecks_service.healthchecks_signal_fail()

            except Exception as e:
                self.logger_service.log.error(f"Job failed: {e}")
                await self.healthchecks_service.healthchecks_signal_fail()
            finally:
                self.logger_service.debug("OsintJob finished")
                await asyncio.sleep(10 * 60)
