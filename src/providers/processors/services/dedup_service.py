from typing import List, Dict
from nest.core import Injectable
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from telethon.tl.types import Message
from src.providers.logger.logger_service import Logger
from src.providers.openai.services.openai_service import OpenAIClientService
from src.providers.telegram.telegram_document import TelegramMessage

BATCH_SIZE = 100  # Number of messages to process per batch for embeddings


@Injectable()
class DeduplicationService:
    def __init__(
        self,
        openai_client_service: OpenAIClientService,
        logger_service: Logger,
    ):
        self.openai_client_service = openai_client_service
        self.logger_service = logger_service

    def deduplicate_messages(
        self,
        messages: List[TelegramMessage],
        similarity_threshold: float = 0.925,
    ) -> List[TelegramMessage]:
        """
        Deduplicate messages based on similarity using embeddings.

        Args:
            messages (List[Message]): List of messages to deduplicate.
            similarity_threshold (float): Threshold above which messages are considered duplicates.

        Returns:
            List[Message]: List of deduplicated messages.
        """
        if not messages:
            return []

        # Extract message texts
        message_texts: list[str] = [message.content for message in messages]

        # Generate embeddings using OpenAIClientService
        embeddings = self.openai_client_service.get_embeddings(message_texts)

        if embeddings is None:
            self.logger_service.log.error(
                "Failed to generate embeddings for deduplication."
            )
            return messages  # Return original messages if embeddings fail

        # Convert embeddings to NumPy array
        embeddings_array = np.array(embeddings)

        # Compute cosine similarity matrix
        similarity_matrix = cosine_similarity(embeddings_array)

        # Identify duplicates
        messages_to_remove = set()
        num_messages = len(messages)
        for i in range(num_messages):
            if i in messages_to_remove:
                continue
            for j in range(i + 1, num_messages):
                if j in messages_to_remove:
                    continue
                similarity = similarity_matrix[i][j]
                if similarity >= similarity_threshold:
                    messages_to_remove.add(j)

        # Filter out duplicate messages
        deduplicated_messages = [
            msg for idx, msg in enumerate(messages) if idx not in messages_to_remove
        ]

        return deduplicated_messages
