from nest.core import Module

from src.providers.processors.services.llm_pipeline_service import LLMPipelineService
from src.providers.processors.services.ner_service import NERService
from src.providers.processors.services.translation_service import TranslationService


@Module(
    providers=[TranslationService, NERService, LLMPipelineService],
    exports=[LLMPipelineService],
)
class ProcessorsModule:
    pass
