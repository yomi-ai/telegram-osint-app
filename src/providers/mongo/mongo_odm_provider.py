import os
from ast import Index
from typing import List

from beanie import Document, init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from nest.core.database.odm_config import ConfigFactory

from src.providers.config.config_service import ConfigService


class MongoODMProvider:
    """
    Provides an interface for working with an ODM (Object-Document Mapping).

    Args:
        db_type (str, optional): The type of database. Defaults to "mongodb".
        config_params (dict, optional): Configuration parameters specific to the chosen database type.
                                        Defaults to None.
        document_models (beanie.Document): a list of beanie.Document instances

    Attributes:
        config: The configuration factory for the chosen database type.
        config_url: The URL generated from the database configuration parameters.
    """

    def __init__(
        self,
        db_type="mongodb",
        config_params: dict = None,
        document_models: list[Document] = None,
    ):
        """
        Initializes the OrmService instance.

        Args:
            db_type (str, optional): The type of database. Defaults to "mongodb".
            config_params (dict, optional): Configuration parameters specific to the chosen database type.
                                            Defaults to None.
        """
        self.config_object = ConfigFactory(db_type=db_type).get_config()
        self.config = self.config_object(**config_params)
        self.config_url = self.build_mongo_uri()  # Call the method to build the URI
        self.document_models: list[Document] = document_models
        self.check_document_models()

    def build_mongo_uri(self) -> str:
        """
        Build the MongoDB connection URI based on the provided config.
        Supports both experiment and prod clusters.
        """
        db_user = self.config.user
        db_password = self.config.password
        db_host = self.config.host

        return f"mongodb+srv://{db_user}:{db_password}@{db_host}/?retryWrites=true&w=majority&appName=telegram-osint-app"

    async def create_all(self):
        """
        Initialize the database and the document models with Beanie.
        """
        self.check_document_models()
        client = AsyncIOMotorClient(self.config_url)
        await init_beanie(
            database=client[self.config.db_name], document_models=self.document_models
        )

    def check_document_models(self):
        """
        Checks that the document_models argument is a list of beanie.Document instances.
        """
        if not isinstance(self.document_models, list):
            raise Exception("document_models should be a list")
        for document_model in self.document_models:
            if not issubclass(document_model, Document):
                raise Exception(
                    "Each item in document_models should be a subclass of beanie.Document"
                )
