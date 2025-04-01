"""
Region Jobs Module

This module defines job classes for processing Telegram messages for specific regions.
Each region (geographic area) has its own job class that inherits from a base class.

The jobs are responsible for:
1. Fetching messages from Telegram channels for their specific region
2. Processing these messages through the LLM pipeline
3. Sending the processed messages to the appropriate output channel

These jobs are designed to be run by a coordinator that executes them sequentially.
"""

import asyncio
from nest.core import Injectable
from src.providers.logger.logger_service import Logger
from src.providers.telegram.telegram_service import TelegramService
from src.providers.processors.services.llm_pipeline_service import LLMPipelineService
from src.providers.healthchecks.healthchecks_service import HealthchecksService


@Injectable()
class RegionOsintJob:
    """
    Base class for region-specific OSINT jobs.
    
    This class provides the core functionality for processing messages for a specific
    geographic region. It is designed to be subclassed for each region, with the
    subclass specifying the region name.
    
    The job fetches messages from Telegram channels for its region, processes them
    through the LLM pipeline, and sends the processed messages to the appropriate
    output channel.
    """

    def __init__(
        self,
        telegram_service: TelegramService,
        llm_pipeline_service: LLMPipelineService,
        logger_service: Logger,
        healthchecks_service: HealthchecksService,
    ):
        """
        Initialize the region OSINT job.
        
        Args:
            telegram_service: Service for interacting with Telegram
            llm_pipeline_service: Service for processing messages through the LLM pipeline
            logger_service: Service for logging
            healthchecks_service: Service for sending health check signals
        """
        self.telegram_service = telegram_service
        self.llm_pipeline_service = llm_pipeline_service
        self.logger_service = logger_service
        self.healthchecks_service = healthchecks_service
        self.region = "base"  # Will be overridden by subclasses

    async def process_region(self):
        """
        Process messages for this region.
        
        This method:
        1. Fetches messages from Telegram channels for this region
        2. Processes these messages through the LLM pipeline
        3. Sends the processed messages to the appropriate output channel
        
        Returns:
            True if processing was successful, False otherwise
        """
        try:
            start_time = asyncio.get_event_loop().time()
            self.logger_service.info(
                f"[{self.region}] Starting processing at {start_time}"
            )

            # Retrieve messages from telegram for this region
            telegram_messages = await self.telegram_service.fetch_messages_for_region(
                self.region
            )

            if not telegram_messages:
                self.logger_service.info(f"No messages found for region: {self.region}")
                return True

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
                            f"Sending message to {self.region} channel - message: \n{message_to_send}\n"
                        )
                        await self.telegram_service.send_message_to_region(
                            self.region, message_to_send
                        )
                        await asyncio.sleep(5)
            except Exception as e:
                self.logger_service.error(
                    f"Failed to send message for {self.region} due to {e}"
                )
                return False

            end_time = asyncio.get_event_loop().time()
            duration = end_time - start_time
            self.logger_service.info(
                f"[{self.region}] Finished processing in {duration:.2f} seconds"
            )
            return True
        except Exception as e:
            self.logger_service.error(f"[{self.region}] Error processing: {e}")
            return False


@Injectable()
class HebronOsintJob(RegionOsintJob):
    """
    Hebron-specific OSINT job.
    
    This job processes messages for the Hebron region, using the configuration
    defined in the telegram_model.py file for Hebron.
    """

    def __init__(
        self,
        telegram_service: TelegramService,
        llm_pipeline_service: LLMPipelineService,
        logger_service: Logger,
        healthchecks_service: HealthchecksService,
    ):
        """
        Initialize the Hebron OSINT job.
        
        Args:
            telegram_service: Service for interacting with Telegram
            llm_pipeline_service: Service for processing messages through the LLM pipeline
            logger_service: Service for logging
            healthchecks_service: Service for sending health check signals
        """
        super().__init__(
            telegram_service, llm_pipeline_service, logger_service, healthchecks_service
        )
        self.region = "hebron"


@Injectable()
class EtzionOsintJob(RegionOsintJob):
    """
    Etzion-specific OSINT job.
    
    This job processes messages for the Etzion region, using the configuration
    defined in the telegram_model.py file for Etzion.
    """

    def __init__(
        self,
        telegram_service: TelegramService,
        llm_pipeline_service: LLMPipelineService,
        logger_service: Logger,
        healthchecks_service: HealthchecksService,
    ):
        """
        Initialize the Etzion OSINT job.
        
        Args:
            telegram_service: Service for interacting with Telegram
            llm_pipeline_service: Service for processing messages through the LLM pipeline
            logger_service: Service for logging
            healthchecks_service: Service for sending health check signals
        """
        super().__init__(
            telegram_service, llm_pipeline_service, logger_service, healthchecks_service
        )
        self.region = "etzion"
