import os

from dotenv import load_dotenv
from nest.core import Injectable

load_dotenv()


class DynamicConfig:
    _ENVIRONMENT_MAP = {}

    def __init__(self):
        self.load_configs()

    def load_configs(self):
        env_vars = os.environ
        for key, value in env_vars.items():
            self._ENVIRONMENT_MAP[key] = value

    def get(self, key: str, default=None):
        return self._ENVIRONMENT_MAP.get(key, default)


@Injectable()
class ConfigService:
    def __init__(self):
        self._config = DynamicConfig()

    @property
    def config(self):
        return self._config

    def get(self, key: str, default_value=None):
        return self.config.get(key, default_value)
