from pydantic import BaseModel, BaseSettings


class TelegramSettings(BaseSettings):
    SESSION_NAME: str = "session_name"
    FETCH_LIMIT: int = 100
    MESSAGE_FILTER_INTERVAL_MINUTES: int = 100
