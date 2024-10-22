import os

from dotenv import load_dotenv

from nest.core.database.odm_provider import OdmProvider
from src.providers.telegram.telegram_document import TelegramMessage
from beanie import Document


load_dotenv()

config = OdmProvider(
    config_params={
        "db_name": os.getenv("MONGO_DB_NAME", "default_nest_db"),
        "host": os.getenv("MONGO_DB_HOST", "localhost"),
        "port": os.getenv("MONGO_DB_PORT", 27017),
        "user": os.getenv("MONGO_DB_USERNAME", "root"),
        "password": os.getenv("MONGO_DB_PASSWORD", "password"),
    },
    document_models=[TelegramMessage],
)
