from nest.core import Module

from .logger_service import Logger


@Module(
    providers=[Logger],
    exports=[Logger],
)
class LoggerModule: ...
