import os
from enum import Enum
from typing import Any, Dict

from dotenv import load_dotenv
from nest.core import Injectable
from pydantic import BaseSettings


class AppContext(BaseSettings):
    STAGE = os.environ.get("STAGE", "local")
    APP_NAME = os.environ.get("APP_NAME", "app")
    APP_VERSION = os.environ.get("APP_VERSION", "0.0.1")
    APP_DESCRIPTION = os.environ.get("APP_DESCRIPTION", "App description")
    APP_DEBUG = os.environ.get("APP_DEBUG", False)


class DynamicConfig:
    _ENVIRONMENT_MAP = {}

    def __init__(self, app_context: AppContext = None):
        self.app_context = app_context
        self.load_configs()

    def load_configs(self):
        if self.app_context.STAGE == "local":
            load_dotenv()
        env_vars = os.environ
        for key, value in env_vars.items():
            self._ENVIRONMENT_MAP[key] = value
        for key, value in self.app_context.dict().items():
            self._ENVIRONMENT_MAP[key] = value

    def get(self, key: str, default=None):
        return self._ENVIRONMENT_MAP.get(key, default)


@Injectable()
class ConfigService:
    def __init__(self):
        self._app_context = AppContext()
        self._config = DynamicConfig(app_context=self.app_context)

    @property
    def app_context(self):
        return self._app_context

    @property
    def config(self):
        return self._config

    def get(self, key: str, default_value=None):
        return self.config.get(key, default_value)

    @app_context.setter
    def app_context(self, value):
        self._app_context = value
