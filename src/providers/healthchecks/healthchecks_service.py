import httpx
from nest.core import Injectable

from src.providers.config.config_service import ConfigService
from src.providers.logger.logger_service import Logger


@Injectable()
class HealthchecksService:
    MISSING_KEY_MESSAGE = "Please set HEALTHCHECKS_PING_KEY, otherwise you will keep seeing this this warning"

    def __init__(
        self,
        config_service: ConfigService,
        logger: Logger
    ):
        self.config_service = config_service
        self.logger_service = logger
        self.healthchecks_ping_key = self.config_service.get("HEALTHCHECKS_PING_KEY")
        if self.healthchecks_ping_key is None:
            self.logger_service.log.warning(self.MISSING_KEY_MESSAGE)
        self.healthchecks_ping_url = f"https://hc-ping.com/{self.healthchecks_ping_key}/telegram-osint-app"
    
    async def _healthchecks_ping(self, url):
        if self.healthchecks_ping_key is None:
            self.logger_service.log.warning(self.MISSING_KEY_MESSAGE)
            return
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url)
                response.raise_for_status()
            except Exception as e:
                self.logger_service.log.error(e)
    
    async def healthchecks_signal_start(self):
        return await self._healthchecks_ping(self.healthchecks_ping_url+"/start")
    
    async def healthchecks_signal_fail(self):
        return await self._healthchecks_ping(self.healthchecks_ping_url+"/fail")
    
    async def healthchecks_signal_success(self):
        return await self._healthchecks_ping(self.healthchecks_ping_url)