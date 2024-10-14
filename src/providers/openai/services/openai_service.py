# src/services/openai_client_service.py
import base64
import os
from typing import Optional

import openai
from dotenv import load_dotenv
from nest.core import Injectable
from pydantic import BaseModel

from src.providers.config.config_service import ConfigService
from src.providers.cost_calculator.services.cost_calculator_service import (
    CostCalculatorService,
)

# Load environment variables from a .env file
load_dotenv()

# Set your OpenAI API key from the environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")


@Injectable()
class OpenAIClientService:
    """Service class to interact with OpenAI API and calculate costs."""

    def __init__(
        self,
        config_service: ConfigService,
        cost_calculator_service: CostCalculatorService,
    ):
        self.config_service = config_service
        self.model_name = self.config_service.get("MODEL_NAME")
        self.cost_calculator_service = cost_calculator_service

        # Track total costs across multiple calls
        self.total_prompt_cost = 0.0
        self.total_completion_cost = 0.0

    @staticmethod
    def _encode_image(image_path: str) -> Optional[str]:
        """Encode an image from a file path to a base64 string."""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        except Exception as e:
            print(f"Error encoding image: {e}")
            return None

    def _prepare_messages(
        self, system_message: str, user_message: str, image_path: Optional[str] = None
    ):
        """Prepare messages to be sent to the API, with optional image encoding."""
        messages = [{"role": "system", "content": system_message}]

        # Prepare user content
        if image_path:
            base64_image = self._encode_image(image_path)
            if base64_image:
                user_content = [
                    {"type": "text", "text": user_message},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ]
            else:
                user_content = user_message
        else:
            user_content = user_message

        messages.append({"role": "user", "content": user_content})
        return messages

    def _build_api_payload(
        self,
        messages,
        response_format: Optional[BaseModel] = None,
        max_tokens: Optional[int] = None,
    ):
        """Build the payload for the OpenAI API request."""
        api_payload = {
            "model": self.model_name,
            "messages": messages,
        }
        if response_format:
            api_payload["response_format"] = response_format
        if max_tokens:
            api_payload["max_tokens"] = max_tokens

        return api_payload

    @staticmethod
    def _make_api_call(api_payload):
        """Make the API call and return the response or handle exceptions."""
        try:
            return openai.ChatCompletion.create(**api_payload)
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return None

    @staticmethod
    def _handle_response(response):
        """Handle the response from the API."""
        if response and response.choices:
            message = response.choices[0].message
            if hasattr(message, "parsed") and message.parsed:
                return message.parsed
            elif hasattr(message, "refusal") and message.refusal:
                print("Model refused to process the request.")
                return message.refusal
            else:
                return message.content
        return None

    def _calculate_cost(self, messages, response):
        """Calculate and accumulate the cost of the prompt and completion."""
        # Calculate prompt cost
        full_prompt = self._extract_full_prompt(messages)
        has_image = self._check_for_image(messages)
        prompt_cost = self.cost_calculator_service.calculate_prompt_cost(
            full_prompt, has_image=has_image
        )
        self.total_prompt_cost += prompt_cost

        # Calculate completion cost if response is available
        if response and response.choices:
            completion_text = response.choices[0].message.content
            completion_cost = self.cost_calculator_service.calculate_completion_cost(
                completion_text
            )
            self.total_completion_cost += completion_cost

    @staticmethod
    def _extract_full_prompt(messages):
        """Extracts the full prompt text from messages."""
        full_prompt = ""
        for msg in messages:
            content = msg.get("content")
            if isinstance(content, list):
                for item in content:
                    if "text" in item:
                        full_prompt += item["text"]
            elif isinstance(content, str):
                full_prompt += content
        return full_prompt

    @staticmethod
    def _check_for_image(messages):
        """Checks if any message content includes an image."""
        for msg in messages:
            content = msg.get("content")
            if isinstance(content, list):
                if any(item.get("type") == "image_url" for item in content):
                    return True
        return False

    def chat(
        self,
        system_message: str,
        user_message: str,
        image_path: Optional[str] = None,
        response_format: Optional[BaseModel] = None,
        max_tokens: Optional[int] = 300,
    ):
        """Main method to send a chat request to OpenAI with optional image input."""

        # Step 1: Prepare messages
        messages = self._prepare_messages(system_message, user_message, image_path)

        # Step 2: Build API payload
        api_payload = self._build_api_payload(messages, response_format, max_tokens)

        # Step 3: Make the API call
        response = self._make_api_call(api_payload)

        # Step 4: Handle and return the response
        response_result = self._handle_response(response)

        # Step 5: Calculate and accumulate prompt and completion costs
        self._calculate_cost(messages, response)

        return response_result

    def print_total_costs(self):
        """Prints the total accumulated prompt, completion, and overall costs."""
        total_cost = self.total_prompt_cost + self.total_completion_cost
        print(f"Total prompt cost: ${self.total_prompt_cost:.6f}")
        print(f"Total completion cost: ${self.total_completion_cost:.6f}")
        print(f"Overall total cost: ${total_cost:.6f}")
