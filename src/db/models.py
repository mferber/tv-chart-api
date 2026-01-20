from typing import Literal, TypedDict

from advanced_alchemy.base import UUIDAuditBase
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship

from setup.litestar_users.models import User


class EpisodeInfo(TypedDict):
    season: int
    index: int
    type: Literal["special", "episode"]
    watched: bool


class SeasonInfo(TypedDict):
    number: int
    episodes: list[EpisodeInfo]


class Show(UUIDAuditBase):
    __tablename__ = "show"

    user_id: Mapped[int] = mapped_column(ForeignKey("user_account.id"))
    tvmaze_id: Mapped[int]
    title: Mapped[str] = mapped_column(String(100))
    source: Mapped[str] = mapped_column(String(50), nullable=True)
    duration: Mapped[int] = mapped_column(nullable=True)
    seasons: Mapped[list[SeasonInfo]] = mapped_column(
        MutableList.as_mutable(JSONB), default=list
    )

    user: Mapped["User"] = relationship()

    def as_text(self) -> str:
        itms = [f"{self.title}"]
        if self.source is not None:
            itms.append(self.source)
        if self.duration is not None:
            itms.append(f"{self.duration} min.")
        itms.extend(self._serialize_episodes_descriptor())
        return "\n".join(itms)

    def _serialize_episodes_descriptor(self) -> list[str]:
        season_strs = []
        if self.seasons is not None:
            for season in self.seasons:
                season_chars = []
                if season["episodes"] is not None:
                    for episode in season["episodes"]:
                        if episode["type"] == "special":
                            episode_char = "S" if episode["watched"] else "s"
                        else:
                            episode_char = "X" if episode["watched"] else "."
                        season_chars.append(episode_char)
                    season_strs.append("".join(season_chars))
        return season_strs
