from nest.core import Module

from .openai_service import OpenaiService


@Module(
    providers=[OpenaiService],
    exports=[OpenaiService]
)   
class OpenaiModule:
    pass
