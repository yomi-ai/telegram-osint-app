from nest.core import Module

from src.providers.openai.services.openai_service import OpenaiService


@Module(providers=[OpenaiService], exports=[OpenaiService])
class OpenaiModule:
    pass
