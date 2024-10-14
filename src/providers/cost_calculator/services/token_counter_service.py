import tiktoken
from nest.core import Injectable


@Injectable()
class TokenCounterService:
    def __init__(self, default_encoding: str = "o200k_base"):
        self.model_encoding_map = {
            "gpt-4o": "o200k_base",
            "gpt-4o-mini": "o200k_base",
            "gpt-4-turbo": "cl100k_base",
            "gpt-4": "cl100k_base",
            "gpt-3.5-turbo": "cl100k_base",
            "text-embedding-ada-002": "cl100k_base",
            "text-embedding-3-small": "cl100k_base",
            "text-embedding-3-large": "cl100k_base",
            "Codex": "p50k_base",
            "text-davinci-002": "p50k_base",
            "text-davinci-003": "p50k_base",
            "davinci": "r50k_base",
        }
        self.default_encoding = default_encoding

    def num_tokens_from_string(self, string: str, model_name: str) -> int:
        encoding_name = self.model_encoding_map.get(model_name, self.default_encoding)
        encoding = tiktoken.get_encoding(encoding_name)
        num_tokens = len(encoding.encode(string))
        return num_tokens

    def find_closest_model(self, input_model: str) -> str | None:
        for model in self.model_encoding_map:
            if model in input_model:
                return model
        return None
