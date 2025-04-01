"""
Region Coordinator Module

This module defines a coordinator job that sequentially runs region-specific jobs.
The coordinator is responsible for:
1. Running each region job in sequence
2. Tracking the overall success/failure of the processing cycle
3. Sending health check signals
4. Managing the job execution interval

This approach ensures that regions are processed one after another, avoiding
any potential issues with concurrent Telegram API access.
"""

import asyncio
from nest.core import Injectable
from src.providers.logger.logger_service import Logger
from src.providers.healthchecks.healthchecks_service import HealthchecksService
from src.jobs.region_jobs import HebronOsintJob, EtzionOsintJob


@Injectable()
class RegionCoordinatorJob:
    """
    Coordinator job that runs region jobs sequentially.
    
    This job is responsible for coordinating the execution of region-specific jobs.
    It runs each region job in sequence, tracks the overall success/failure,
    and manages the job execution interval.
    """

    def __init__(
        self,
        logger_service: Logger,
        healthchecks_service: HealthchecksService,
        hebron_job: HebronOsintJob,
        etzion_job: EtzionOsintJob,
    ):
        """
        Initialize the region coordinator job.
        
        Args:
            logger_service: Service for logging
            healthchecks_service: Service for sending health check signals
            hebron_job: Job for processing Hebron region
            etzion_job: Job for processing Etzion region
        """
        self.logger_service = logger_service
        self.healthchecks_service = healthchecks_service
        self.hebron_job = hebron_job
        self.etzion_job = etzion_job
        self.is_running = False
        self.interval_minutes = 10

    async def process_all_regions(self):
        """
        Process all regions sequentially.
        
        This method runs each region job in sequence and tracks the overall success/failure.
        
        Returns:
            True if all regions were processed successfully, False otherwise
        """
        overall_success = True

        # Process Hebron region
        self.logger_service.info("Starting Hebron region processing")
        hebron_success = await self.hebron_job.process_region()
        if not hebron_success:
            overall_success = False
            self.logger_service.error("Hebron region processing failed")

        # Process Etzion region
        self.logger_service.info("Starting Etzion region processing")
        etzion_success = await self.etzion_job.process_region()
        if not etzion_success:
            overall_success = False
            self.logger_service.error("Etzion region processing failed")

        return overall_success

    async def run(self):
        """
        Main job loop that processes all regions sequentially.
        
        This method runs in an infinite loop, processing all regions at the specified
        interval. It sends health check signals to indicate the job's status.
        """
        self.logger_service.info("Starting Region Coordinator Job")
        self.is_running = True

        while self.is_running:
            await self.healthchecks_service.healthchecks_signal_start()

            try:
                self.logger_service.info("Running region processing cycle")
                success = await self.process_all_regions()

                if success:
                    await self.healthchecks_service.healthchecks_signal_success()
                else:
                    await self.healthchecks_service.healthchecks_signal_fail()

            except Exception as e:
                self.logger_service.log.error(f"Region coordinator job failed: {e}")
                await self.healthchecks_service.healthchecks_signal_fail()
            finally:
                self.logger_service.debug("Region processing cycle finished")
                await asyncio.sleep(self.interval_minutes * 60)

    async def stop(self):
        """
        Stop the job.
        
        This method is called during application shutdown to gracefully stop the job.
        """
        self.is_running = False
        self.logger_service.info("Stopping Region Coordinator Job")
