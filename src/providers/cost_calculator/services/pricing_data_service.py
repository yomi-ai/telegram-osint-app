import requests
from nest.core import Injectable


@Injectable()
class PricingDataService:
    def __init__(self):
        self.pricing_url = "https://raw.githubusercontent.com/BerriAI/litellm/refs/heads/main/model_prices_and_context_window.json"
        self.pricing_data = self._fetch_pricing_data()

    def _fetch_pricing_data(self) -> dict:
        response = requests.get(self.pricing_url)
        if response.status_code == 200:
            return response.json()
        else:
            raise ValueError(
                f"Failed to fetch pricing data. Status code: {response.status_code}"
            )

    def get_pricing_data(self) -> dict:
        return self.pricing_data
