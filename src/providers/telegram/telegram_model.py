from pydantic import BaseModel, BaseSettings


class TelegramSettings(BaseSettings):
    SESSION_NAME: str = "session_name"
    FETCH_LIMIT: int = 1000
    MESSAGE_FILTER_INTERVAL_MINUTES: int = 10
