from nest.core import Injectable

from src.providers.logger.logger_service import Logger
from src.providers.openai.services.openai_service import OpenAIClientService
from src.providers.processors.processors_model import TranslationResponse


@Injectable()
class TranslationService:
    def __init__(self, client: OpenAIClientService, logger: Logger):
        self.client = client
        self.logger = logger

    def translate(self, message: str) -> TranslationResponse:
        system_message = """
            Act as a highly accurate translator. Your task is to take an Arabic message from a Telegram group 
            and translate it into both Hebrew and English. Follow the guidelines provided earlier.
        """
        try:
            response = self.client.chat(
                system_message=system_message,
                user_message=message,
                response_format=TranslationResponse,
            )
            return response
        except Exception as e:
            self.logger.log.error(f"Failed to translate message: {e}")
            raise e
