from nest.core import Injectable
from src.providers.cost_calculator.services.token_counter_service import (
    TokenCounterService,
)
from src.providers.cost_calculator.services.pricing_data_service import (
    PricingDataService,
)


@Injectable()
class ModelResolverService:
    def __init__(
        self,
        token_counter: TokenCounterService,
        pricing_data_service: PricingDataService,
    ):
        self.token_counter = token_counter
        self.pricing_data_service = pricing_data_service
        self.pricing_data = self.pricing_data_service.get_pricing_data()

    def resolve_encoding_model(self, model_name: str) -> str:
        encoding_model = self.token_counter.find_closest_model(model_name)
        if encoding_model:
            return encoding_model
        else:
            raise ValueError(f"No encoding found for model '{model_name}'.")

    def resolve_pricing_model(self, model_name: str) -> str:
        if model_name in self.pricing_data:
            return model_name
        else:
            pricing_model = self._find_closest_pricing_model(model_name)
            if pricing_model:
                return pricing_model
            else:
                raise ValueError(f"No pricing found for model '{model_name}'.")

    def _find_closest_pricing_model(self, input_model: str) -> str | None:
        for model in self.pricing_data:
            if model in input_model:
                return model
        return None
