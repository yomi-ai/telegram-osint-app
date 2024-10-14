import openai
from nest.core import Injectable

from src.providers.config.config_service import ConfigService


@Injectable
class OpenaiService:

    def __init__(self, config_service: ConfigService):
        self.config_service = config_service
        self._set_openai_key()

    def _set_openai_key(self):
        openai.api_key = self.config_service.get("OPENAI_API_KEY")

    def translate_text(self, text: str, language: str):
        response = openai.Completion.create(
            engine="davinci",
            prompt=f"Translate the following Arabic text into hebrew",
            max_tokens=60,
        )
        return response.choices[0].text
