from typing import List, Tuple

import numpy as np
from nest.core import Injectable
from sklearn.metrics.pairwise import cosine_similarity

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
            messages (List[TelegramMessage]): List of messages to deduplicate.
            similarity_threshold (float): Threshold above which messages are considered duplicates.

        Returns:
            List[TelegramMessage]: List of deduplicated messages.
        """
        if not messages:
            return []

        # Extract message texts
        message_texts = [message.content for message in messages]

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

    def is_similar_to_any(
        self,
        target_message: TelegramMessage,
        other_messages: List[TelegramMessage],
        similarity_threshold: float = 0.925,
    ) -> Tuple[bool, List[TelegramMessage]]:
        """
        Checks if the target message is too similar to any message in a list of other messages.

        Args:
            target_message (TelegramMessage): The message to check for similarity.
            other_messages (List[TelegramMessage]): List of other messages to compare against.
            similarity_threshold (float): Threshold above which messages are considered duplicates.

        Returns:
            Tuple[bool, List[TelegramMessage]]: A tuple containing a boolean indicating similarity and a list of similar messages.
        """
        if not other_messages:
            return False, []

        # Get embeddings for the target message and other messages
        target_embedding = self.openai_client_service.get_embeddings(
            [target_message.content]
        )
        if not target_embedding:
            self.logger_service.log.error(
                "Failed to generate embedding for target message."
            )
            return False, []
        target_embedding = target_embedding[0]

        other_texts = [msg.content for msg in other_messages]
        other_embeddings = self.openai_client_service.get_embeddings(other_texts)
        if not other_embeddings:
            self.logger_service.log.error(
                "Failed to generate embeddings for other messages."
            )
            return False, []

        # Calculate cosine similarity between target message and each other message
        similarities = cosine_similarity([target_embedding], other_embeddings)[0]

        # Identify messages exceeding the similarity threshold
        similar_indices = [
            i
            for i, similarity in enumerate(similarities)
            if similarity >= similarity_threshold
        ]

        if similar_indices:
            similar_messages = [other_messages[i] for i in similar_indices]
            return True, similar_messages
        else:
            return False, []
