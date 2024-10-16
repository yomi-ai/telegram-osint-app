from typing import List

from pydantic import BaseModel


class TranslationResponse(BaseModel):
    hebrew: str
    english: str


class NERResponse(BaseModel):
    locations: List[str]
    people: List[str]
    organizations: List[str]
