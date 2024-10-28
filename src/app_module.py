import asyncio

import uvicorn
from nest.core import Controller, Get, Injectable, Module, PyNestFactory

from src.app_controller import AppController
from src.app_service import AppService
from src.jobs.osint_event_handler import OsintEventhandler
from src.mongo_config import config


@Module(controllers=[AppController], providers=[AppService, OsintEventhandler])
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
    await config.create_all()
    osint_event_handler: OsintEventhandler = app.container.get_instance(
        OsintEventhandler
    )
    asyncio.create_task(osint_event_handler.start_event_handler())
