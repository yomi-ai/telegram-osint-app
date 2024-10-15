from nest.core import Injectable

from src.providers.openai.services.openai_service import OpenAIClientService
from src.providers.processors.processors_model import NERResponse


@Injectable()
class NERService:
    def __init__(self, client: OpenAIClientService):
        self.client = client

    def extract_entities(self, message: str) -> NERResponse:
        system_message = """
            Act as an entity recognition system. Your task is to extract locations, people, 
            and organizations from the provided Arabic Telegram message.
        """
        response = self.client.chat(
            system_message=system_message,
            user_message=message,
            response_format=NERResponse,
        )
        return response
