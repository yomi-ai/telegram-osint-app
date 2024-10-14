from nest.core import Module

from .logger_service import LoggerService


@Module(
    providers=[LoggerService],
    exports=[LoggerService],
)
class LoggerModule: ...
