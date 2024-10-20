from src.providers.cost_calculator.services.model_resolver_service import ModelResolverService
from src.providers.cost_calculator.services.pricing_data_service import PricingDataService
from src.providers.cost_calculator.services.token_counter_service import TokenCounterService
from src.providers.processors.services.ner_service import NERService
from src.providers.openai.services.openai_service import OpenAIClientService
from src.providers.processors.services.dedup_service import DeduplicationService
from src.providers.processors.services.llm_pipeline_service import LLMPipelineService
from src.providers.telegram.telegram_service import TelegramService
from src.providers.processors.services.translation_service import TranslationService
from src.providers.config.config_service import ConfigService
from src.providers.logger.logger_service import Logger
from src.providers.cost_calculator.services.cost_calculator_service import CostCalculatorService
import asyncio
import faust

# We have to inject the dependencies
config_service = ConfigService()
logger = Logger(config_service)
token_counter_service = TokenCounterService()
pricing_data_service = PricingDataService()
model_resolver_service = ModelResolverService(token_counter_service, pricing_data_service)
cost_calculator_service = CostCalculatorService(config_service, model_resolver_service, token_counter_service, pricing_data_service)
openai_client_service = OpenAIClientService(config_service, cost_calculator_service, logger)
translation_service = TranslationService(openai_client_service)
ner_service = NERService(openai_client_service)
dedup_service = DeduplicationService(config_service, logger)

llm_pipeline_service = LLMPipelineService(translation_service, ner_service)
telegram_service = TelegramService(config_service, logger, dedup_service)

app = faust.App(
    'telegram_osint_app',
    broker='kafka://' + config_service.get("KAFKA_BROKER", "localhost:9092"),
    value_serializer='pickle',
    topic_partitions=1,
    topic_replication_factor=1,
)

osint_jobs_topic = app.topic('osint_jobs')

@app.agent(osint_jobs_topic)
async def parse_messages(stream):

    async for telegram_messages in stream:
        print(f"Parsing {telegram_messages.shape[0]} messages...")

        failed_messages = []

        df = llm_pipeline_service.process_dataframe(telegram_messages)
        for _, row in df.iterrows():
            message_to_send = row["hebrew_translation"]
            success = await telegram_service.send_message_to_channel(message_to_send)
            if not success:
                failed_messages.append(message_to_send if message_to_send else "<<EMPTY MESSAGE>>")
            await asyncio.sleep(10)
        yield failed_messages