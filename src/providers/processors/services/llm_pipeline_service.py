import json
from pathlib import Path

import pandas as pd
from nest.core import Injectable
from tqdm import tqdm

from src.providers.processors.services.ner_service import NERService
from src.providers.processors.services.translation_service import TranslationService


@Injectable()
class LLMPipelineService:
    ABS_PATH = Path(__file__).resolve().parent.parent.parent.parent

    def __init__(self, translator: TranslationService, ner_service: NERService):
        self.translator = translator
        self.ner_service = ner_service

    def process_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["hebrew_translation"] = None
        df["english_translation"] = None
        df["locations"] = None
        df["people"] = None
        df["organizations"] = None

        for index, row in tqdm(
            df.iterrows(), total=len(df), desc="Processing messages"
        ):
            message = row["message"]

            # Translation
            translation = self.translator.translate(message)
            df.at[index, "hebrew_translation"] = translation.hebrew
            df.at[index, "english_translation"] = translation.english

            # NER Extraction
            ner_data = self.ner_service.extract_entities(translation.english)
            df.at[index, "locations"] = ", ".join(ner_data.locations)
            df.at[index, "people"] = ", ".join(ner_data.people)
            df.at[index, "organizations"] = ", ".join(ner_data.organizations)

        self.save_dataframe(df, self.ABS_PATH / "data" / "processed_data.json")

        return df

    @staticmethod
    def save_dataframe(df: pd.DataFrame, file_path: str | Path):
        df.to_json(file_path, index=False)
        return file_path
