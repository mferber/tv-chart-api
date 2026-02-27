from typing import Self
from uuid import UUID

from advanced_alchemy.base import UUIDAuditBase
from advanced_alchemy.types import JsonB
from pydantic import HttpUrl
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as SQLA_UUID
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column

from models.show import EpisodeDescriptor, EpisodeType, Show, ShowCreate


class DbShow(UUIDAuditBase):
    __tablename__ = "show"

    user_id: Mapped[UUID] = mapped_column(
        SQLA_UUID(as_uuid=True), ForeignKey("user_account.id")
    )
    tvmaze_id: Mapped[int]
    title: Mapped[str] = mapped_column(String(100))
    source: Mapped[str] = mapped_column(String(50), nullable=True)
    duration: Mapped[int] = mapped_column(nullable=True)
    image_sm_url: Mapped[str] = mapped_column(String(256), nullable=True)
    image_lg_url: Mapped[str] = mapped_column(String(256), nullable=True)
    imdb_id: Mapped[str] = mapped_column(String(32), nullable=True)
    thetvdb_id: Mapped[int] = mapped_column(Integer, nullable=True)
    seasons: Mapped[list[list[dict]]] = mapped_column(
        MutableList.as_mutable(JsonB), default=list
    )

    @classmethod
    def from_show_model(cls, show: Show | ShowCreate, owner_id: UUID) -> Self:
        json_seasons = [
            [
                {
                    "title": episode_descriptor.title,
                    "type": episode_descriptor.type.value,
                    "watched": episode_descriptor.watched,
                }
                for episode_descriptor in season
            ]
            for season in show.seasons
        ]

        id = show.id if isinstance(show, Show) else None

        return cls(
            id=id,
            user_id=owner_id,
            tvmaze_id=show.tvmaze_id,
            title=show.title,
            source=show.source,
            duration=show.duration,
            image_sm_url=str(show.image_sm_url),
            image_lg_url=str(show.image_lg_url),
            imdb_id=show.imdb_id,
            thetvdb_id=show.thetvdb_id,
            seasons=json_seasons,
        )

    def to_show_model(self) -> Show:
        model_seasons = [
            [
                EpisodeDescriptor(
                    title=episode_info["title"],
                    type=EpisodeType.SPECIAL
                    if episode_info["type"] == "special"
                    else EpisodeType.EPISODE,
                    watched=episode_info["watched"],
                )
                for episode_info in season
            ]
            for season in self.seasons
        ]

        return Show(
            id=self.id,
            tvmaze_id=self.tvmaze_id,
            title=self.title,
            source=self.source,
            duration=self.duration,
            image_sm_url=HttpUrl(self.image_sm_url),
            image_lg_url=HttpUrl(self.image_lg_url),
            imdb_id=self.imdb_id,
            thetvdb_id=self.thetvdb_id,
            seasons=model_seasons,
        )
