import logging

from nest.core import Injectable

from src.providers.config.config_service import ConfigService


@Injectable()
class LoggerService:
    def __init__(
        self,
        config_service: ConfigService,
    ):
        self.config_service = config_service
        self.log = logging.getLogger(__name__)
        self.log.info("LoggerService initialized")
