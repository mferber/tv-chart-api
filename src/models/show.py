from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, HttpUrl


class EpisodeType(StrEnum):
    EPISODE = "episode"
    SPECIAL = "special"


@dataclass
class EpisodeDescriptor:
    type: EpisodeType
    watched: bool


class ShowCreate(BaseModel):
    tvmaze_id: int
    title: str
    source: str
    duration: int
    image_sm_url: HttpUrl | None
    image_lg_url: HttpUrl | None
    seasons: list[list[EpisodeDescriptor]]


class Show(ShowCreate):
    id: UUID
