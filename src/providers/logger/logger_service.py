import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from nest.core import Injectable

from src.providers.config.config_service import ConfigService


class ContextualFilter(logging.Filter):
    """
    A custom log filter to add extra context information to each log.
    This can be extended to include things like request ID, user, or session info.
    """

    def filter(self, log_record):
        log_record.context = "DefaultContext"  # This can be dynamic
        return True


@Injectable()
class Logger:
    def __init__(
        self,
        config_service: ConfigService,
    ):
        """
        Initializes the Logger class and configures the logging handlers and formatters.

        :param config_service: Instance of the ConfigService to fetch the configuration for logging.
        """
        self.config_service = config_service
        self.log = logging.getLogger(self.config_service.get("APP_NAME", __name__))
        if not self.log.hasHandlers():  # Ensure that handlers are added only once
            self.configure_logging()

    def configure_logging(self):
        """
        Configures the logging setup based on the environment and configuration.
        Adds both console and file handlers with proper formatting.
        """
        log_level = self.config_service.get("LOG_LEVEL", "INFO").upper()
        log_file = self.config_service.get("LOG_FILE", "app.log")
        log_max_size = int(
            self.config_service.get("LOG_MAX_SIZE", 10485760)
        )  # 10MB default
        log_backup_count = int(
            self.config_service.get("LOG_BACKUP_COUNT", 5)
        )  # 5 files by default

        # Set the overall log level
        self.log.setLevel(log_level)

        # Create formatters
        console_formatter = logging.Formatter(
            "%(asctime)s %(name)s [%(levelname)s] %(context)s: %(message)s",
            "%Y-%m-%d %H:%M:%S",
        )
        file_formatter = logging.Formatter(
            "%(asctime)s %(name)s [%(levelname)s] %(context)s: %(message)s",
            "%Y-%m-%d %H:%M:%S",
        )

        # Create and configure the console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(ContextualFilter())  # Add filter for context

        # Create and configure the file handler (with rotation)
        log_path = Path(os.path.dirname(log_file))
        log_path.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file, maxBytes=log_max_size, backupCount=log_backup_count
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(file_formatter)
        file_handler.addFilter(ContextualFilter())  # Add filter for context

        # Add handlers to the logger only if they don't already exist
        self.log.addHandler(console_handler)
        self.log.addHandler(file_handler)

        self.log.info("Logger initialized with level %s", log_level)

    def info(self, message: str, *args, **kwargs):
        """
        Log an info level message.
        """
        self.log.info(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        """
        Log an error level message.
        """
        self.log.error(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        """
        Log a warning level message.
        """
        self.log.warning(message, *args, **kwargs)

    def debug(self, message: str, *args, **kwargs):
        """
        Log a debug level message.
        """
        self.log.debug(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs):
        """
        Log a critical level message.
        """
        self.log.critical(message, *args, **kwargs)
