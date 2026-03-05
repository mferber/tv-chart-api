import datetime
from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, HttpUrl


class EpisodeType(StrEnum):
    EPISODE = "episode"
    SPECIAL = "special"


@dataclass
class EpisodeDescriptor:
    title: str | None
    type: EpisodeType
    displayNumber: int | None
    watched: bool


class EpisodeDetails(BaseModel):
    title: str | None
    type: EpisodeType
    duration: int | None
    release_date: datetime.date | None
    summary: str | None


class ShowCreate(BaseModel):
    tvmaze_id: int
    title: str
    source: str
    duration: int
    image_sm_url: HttpUrl | None
    image_lg_url: HttpUrl | None
    imdb_id: str | None
    thetvdb_id: int | None
    seasons: list[list[EpisodeDescriptor]]


class Show(ShowCreate):
    id: UUID
