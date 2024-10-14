from nest.core import Module

from src.providers.telegram.telegram_service import TelegramService


@Module(providers=[TelegramService], exports=[TelegramService])
class TelegramModule:
    pass
