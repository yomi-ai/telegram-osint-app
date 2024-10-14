from nest.core import Injectable

from src.providers.config.config_service import ConfigService
from src.providers.cost_calculator.services.model_resolver_service import (
    ModelResolverService,
)
from src.providers.cost_calculator.services.pricing_data_service import (
    PricingDataService,
)
from src.providers.cost_calculator.services.token_counter_service import (
    TokenCounterService,
)


@Injectable()
class CostCalculatorService:
    IMAGE_COST_PER_MODEL = 0.0021  # Fixed cost per image model used

    def __init__(
        self,
        config_service: ConfigService,
        model_resolver: ModelResolverService,
        token_counter: TokenCounterService,
        pricing_data_service: PricingDataService,
    ):
        self.config_service = config_service
        self.model_name = self.config_service.get("MODEL_NAME")
        self.model_resolver = model_resolver
        self.token_counter = token_counter
        self.pricing_data = pricing_data_service.get_pricing_data()
        self.encoding_model_name = self.model_resolver.resolve_encoding_model(
            self.model_name
        )
        self.pricing_model_name = self.model_resolver.resolve_pricing_model(
            self.model_name
        )

    def calculate_prompt_cost(self, text_prompt: str, has_image: bool = False) -> float:
        num_tokens = self.token_counter.num_tokens_from_string(
            text_prompt, self.encoding_model_name
        )
        input_cost_per_token = self.pricing_data[self.pricing_model_name][
            "input_cost_per_token"
        ]
        text_prompt_cost = num_tokens * input_cost_per_token
        image_cost = self.IMAGE_COST_PER_MODEL if has_image else 0.0
        return text_prompt_cost + image_cost

    def calculate_completion_cost(self, text_completion: str) -> float:
        num_tokens = self.token_counter.num_tokens_from_string(
            text_completion, self.encoding_model_name
        )
        output_cost_per_token = self.pricing_data[self.pricing_model_name][
            "output_cost_per_token"
        ]
        return num_tokens * output_cost_per_token
