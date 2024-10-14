from nest import Module

from .config_service import ConfigService


@Module(
    providers=[ConfigService],
    exports=[ConfigService],
)
class ConfigModule: ...
