# src/services/openai_client_service.py
from __future__ import annotations

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

from typing import List, Optional
from src.providers.logger.logger_service import Logger
from tqdm import tqdm


@Injectable()
class OpenAIClientService:
    BATCH_SIZE = 100
    """Service class to interact with OpenAI API and calculate costs."""

    def __init__(
        self,
        config_service: ConfigService,
        cost_calculator_service: CostCalculatorService,
        logger: Logger,
    ):
        self.config_service = config_service
        self.model_name = "gpt-4o-2024-11-20"
        self.cost_calculator_service = cost_calculator_service
        self.logger = logger
        openai.api_key = self.config_service.get("OPENAI_API_KEY")

        # Track total costs across multiple calls
        self.total_prompt_cost = 0.0
        self.total_completion_cost = 0.0

    def get_embeddings(self, texts: List[str]) -> Optional[List[List[float]]]:
        """
        Generate embeddings for a list of texts using OpenAI's embedding API.

        Args:
            texts (List[str]): List of texts to generate embeddings for.

        Returns:
            Optional[List[List[float]]]: List of embeddings or None if failed.
        """
        embeddings = []
        for i in tqdm(
            range(0, len(texts), self.BATCH_SIZE), desc="Generating embeddings"
        ):
            batch_texts = texts[i : i + self.BATCH_SIZE]
            try:
                response = openai.embeddings.create(
                    input=batch_texts,
                    model=self.config_service.get(
                        "OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002"
                    ),
                )
                batch_embeddings = [message.embedding for message in response.data]
                embeddings.extend(batch_embeddings)
            except Exception as e:
                self.logger.log.error(f"Error generating embeddings: {e}")
                return None  # Return None if there's an error
        return embeddings

    def _encode_image(self, image_path: str) -> str | None:
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

        # If an image path is provided, encode the image and create the image_url
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
        max_completion_tokens: Optional[int] = None,
    ):
        """Build the payload for the OpenAI API request."""
        api_payload = {
            "model": self.model_name,
            "messages": messages,
        }
        if response_format:
            api_payload["response_format"] = response_format
        if max_completion_tokens:
            api_payload["max_completion_tokens"] = max_completion_tokens

        return api_payload

    def _calculate_cost(self, messages, response):
        """Calculate and accumulate the cost of the prompt and completion."""
        # Calculate prompt cost
        full_prompt = "".join([msg["content"] for msg in messages if "content" in msg])
        has_image = any("image_url" in msg["content"] for msg in messages)
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

    def _handle_response(self, response):
        """Handle the response from the API, checking for parsed or refusal states."""
        if response and response.choices:
            completion_text = response.choices[0].message.content

            # Check if the response contains parsed content or refusal
            if response.choices[0].message.parsed:
                return response.choices[0].message.parsed
            elif response.choices[0].message.refusal:
                print("Model refused to process the request.")
                return response.choices[0].message.refusal

        return response

    def _make_api_call(self, api_payload):
        """Make the API call and return the response or handle exceptions."""
        try:
            return openai.beta.chat.completions.parse(**api_payload)
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return None

    def chat(
        self,
        system_message: str,
        user_message: str,
        image_path: Optional[str] = None,
        response_format: Optional[BaseModel] = None,
        max_completion_tokens: Optional[int] = 1000,
    ):
        """Main method to send a chat request to OpenAI with optional image input."""

        # Step 1: Prepare messages
        messages = self._prepare_messages(system_message, user_message, image_path)

        # Step 2: Build API payload
        api_payload = self._build_api_payload(
            messages, response_format, max_completion_tokens
        )

        # Step 3: Make the API call
        response = self._make_api_call(api_payload)

        # Step 4: Handle and return the response
        response_result = self._handle_response(response)

        # Step 5: Calculate and accumulate prompt and completion costs (silently)
        self._calculate_cost(messages, response)

        return response_result

    def print_total_costs(self):
        """Prints the total accumulated prompt, completion, and overall costs."""
        total_cost = self.total_prompt_cost + self.total_completion_cost
        print(f"Total prompt cost: ${self.total_prompt_cost:.6f}")
        print(f"Total completion cost: ${self.total_completion_cost:.6f}")
        print(f"Overall total cost: ${total_cost:.6f}")
