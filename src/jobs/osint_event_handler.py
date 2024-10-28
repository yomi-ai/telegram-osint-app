import asyncio
from datetime import datetime, timedelta

from nest.core import Injectable

from src.providers.healthchecks.healthchecks_service import HealthchecksService
from src.providers.logger.logger_service import Logger
from src.providers.processors.services.dedup_service import DeduplicationService
from src.providers.processors.services.llm_pipeline_service import LLMPipelineService
from src.providers.telegram.telegram_document import TelegramMessage
from src.providers.telegram.telegram_mongo_service import TelegramMongoService
from src.providers.telegram.telegram_service import CHANNELS, TelegramService, events


@Injectable()
class OsintEventhandler:
    def __init__(
        self,
        telegram_service: TelegramService,
        telegram_mongo_service: TelegramMongoService,
        llm_pipeline_service: LLMPipelineService,
        logger_service: Logger,
        healthchecks_service: HealthchecksService,
        dedup_service: DeduplicationService,
    ):
        self.telegram_service = telegram_service
        self.telegram_mongo_service = telegram_mongo_service
        self.llm_pipeline_service = llm_pipeline_service
        self.logger_service = logger_service
        self.healthchecks_service = healthchecks_service
        self.dedup_service = dedup_service

    async def process_event_message(self, event):
        await self.healthchecks_service.healthchecks_signal_start()
        try:
            message = await self.telegram_service.process_new_message(event)
            if not message.relevant_keywords:
                self.logger_service.info(
                    f"message - {message.content} has no relevant keywords, will not sent to channel"
                )
                return
            last_3_hour = datetime.utcnow() - timedelta(
                hours=3
            )  # Fetch messages from the last hour
            recent_messages = (
                await self.telegram_mongo_service.get_messages_with_hebrew_translation(
                    since_timestamp=last_3_hour
                )
            )
            is_similar, similar_messages = self.dedup_service.is_similar_to_any(
                target_message=message, other_messages=recent_messages
            )
            if is_similar:
                self.logger_service.info(
                    f"message - {message.content} too similar to other message - \n{[msg.content for msg in similar_messages]}, will not sent to channel"
                )
                return
            processed_messages = await self.llm_pipeline_service.process_message(
                message
            )
            if processed_messages.hebrew_translation:
                message_to_send = processed_messages.hebrew_translation
                message_to_send += f"\nhttps://t.me/{processed_messages.channel}/{processed_messages.message_id}"
                await self.telegram_service.send_message_to_channel(message_to_send)
                self.logger_service.debug(
                    f"Finish processing message - \nhttps://t.me/{processed_messages.channel}/{processed_messages.message_id}"
                )
            await self.healthchecks_service.healthchecks_signal_success()
        except Exception as e:
            self.logger_service.log.error(e)
            await self.healthchecks_service.healthchecks_signal_fail()

    async def start_event_handler(self):
        """
        Sets up the event handler for new messages.
        """
        async with self.telegram_service.client:
            # Register event listener for new messages in specific channels
            @self.telegram_service.client.on(events.NewMessage(chats=CHANNELS))
            async def handle_new_message(event):
                await self.process_event_message(event)

            # Keep the client running
            await self.telegram_service.client.run_until_disconnected()
