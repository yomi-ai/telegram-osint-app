"""
App Module

This module defines the main application module and startup/shutdown handlers.
It is responsible for:
1. Defining the application's dependency injection container
2. Starting the region coordinator job on application startup
3. Gracefully stopping the job on application shutdown
"""

import asyncio

import uvicorn
from nest.core import Controller, Get, Injectable, Module, PyNestFactory

from src.app_controller import AppController
from src.app_service import AppService
from src.jobs.region_jobs import HebronOsintJob, EtzionOsintJob
from src.jobs.region_coordinator import RegionCoordinatorJob
from src.mongo_config import config


@Module(
    controllers=[AppController],
    providers=[AppService, HebronOsintJob, EtzionOsintJob, RegionCoordinatorJob],
)
class AppModule:
    """
    Main application module.
    
    This module defines the application's dependency injection container,
    including all controllers and providers.
    """
    pass


# Create the application instance
app = PyNestFactory.create(
    AppModule,
    description="Telegram based app for fetching, and processing messages from telegram",
    title="Osint Telegram App",
    version="1.0.0",
)

http_server = app.get_server()


@http_server.on_event("startup")
async def on_startup():
    """
    Application startup handler.
    
    This function is called when the application starts up. It:
    1. Initializes the database
    2. Starts the region coordinator job
    """
    await config.create_all()

    # Start the coordinator job
    coordinator_job: RegionCoordinatorJob = app.container.get_instance(
        RegionCoordinatorJob
    )
    asyncio.create_task(coordinator_job.run())

    app.logger.info("Started region coordinator job")


@http_server.on_event("shutdown")
async def on_shutdown():
    """
    Application shutdown handler.
    
    This function is called when the application is shutting down. It:
    1. Stops the region coordinator job
    """
    # Stop the coordinator job
    coordinator_job: RegionCoordinatorJob = app.container.get_instance(
        RegionCoordinatorJob
    )
    await coordinator_job.stop()

    app.logger.info("Gracefully shut down all jobs and services")
