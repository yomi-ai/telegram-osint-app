from nest.core import Module

from src.providers.cost_calculator.services.cost_calculator_service import (
    CostCalculatorService,
)
from src.providers.cost_calculator.services.model_resolver_service import (
    ModelResolverService,
)
from src.providers.cost_calculator.services.pricing_data_service import (
    PricingDataService,
)
from src.providers.cost_calculator.services.token_counter_service import (
    TokenCounterService,
)


@Module(
    providers=[ModelResolverService, PricingDataService, TokenCounterService],
    exports=[CostCalculatorService],
)
class CostCalculatorModule:
    pass
