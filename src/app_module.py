import asyncio

import uvicorn
from nest.core import Controller, Get, Injectable, Module, PyNestFactory

from src.app_controller import AppController
from src.app_service import AppService
from src.jobs.osint_job import OsintJob


@Module(controllers=[AppController], providers=[AppService, OsintJob])
class AppModule:
    pass


app = PyNestFactory.create(
    AppModule,
    description="Telegram based app for fetching, and processing messages from telegram",
    title="Osint Telegram App",
    version="1.0.0",
)

http_server = app.get_server()


@http_server.on_event("startup")
async def on_startup():
    osint_job: OsintJob = app.container.get_instance(OsintJob)
    asyncio.create_task(osint_job.run())
