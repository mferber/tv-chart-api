"""
Models for TVmaze API responses.
"""

import datetime
from typing import Self

from pydantic import BaseModel, HttpUrl, RootModel

from models.search import SearchResult, SearchResults
from models.show import EpisodeDescriptor, EpisodeType, ShowCreate
from tvmaze_api.utils.html_sanitizer import sanitize_html

# General-use models


class TVmazeCountry(BaseModel):
    name: str


class TVmazeNetwork(BaseModel):
    name: str
    country: TVmazeCountry | None


class TVmazeWebChannel(BaseModel):
    name: str
    country: TVmazeCountry | None


class TVmazeImage(BaseModel):
    medium: HttpUrl | None
    original: HttpUrl | None


class TVmazeExternals(BaseModel):
    imdb: str | None
    thetvdb: int | None


# Episode and show models


class TVmazeEpisode(BaseModel):
    id: int
    name: str | None
    season: int | None
    number: int | None
    type: str
    airdate: str | None
    runtime: int | None
    summary: str | None


class TVmazeEpisodeList(RootModel):
    root: list[TVmazeEpisode]

    def to_episode_models(self) -> list[list[EpisodeDescriptor]]:
        filtered_eps = filter(lambda ep: ep.type != "insignificant_special", self.root)

        seasons: list[list[EpisodeDescriptor]] = []
        current_season: list[EpisodeDescriptor] = []
        current_season_num = 1
        for ep in filtered_eps:
            if ep.season != current_season_num:
                seasons.append(current_season)
                current_season = []
                current_season_num += 1
            episode_type = (
                EpisodeType.EPISODE if ep.type == "regular" else EpisodeType.SPECIAL
            )
            current_season.append(EpisodeDescriptor(type=episode_type, watched=False))
        if current_season:
            seasons.append(current_season)
        return seasons


class TVmazeShow(BaseModel):
    """Encapsulates a show represented in TVmaze's API."""

    id: int
    name: str
    averageRuntime: int | None
    network: TVmazeNetwork | None
    webChannel: TVmazeWebChannel | None
    image: TVmazeImage | None
    externals: TVmazeExternals | None

    def to_show_create_model(self, *, with_episodes: TVmazeEpisodeList) -> ShowCreate:
        if self.network and self.network.name:
            source = self.network.name
        elif self.webChannel and self.webChannel.name:
            source = self.webChannel.name
        else:
            source = "n/a"

        return ShowCreate(
            tvmaze_id=self.id,
            title=self.name,
            source=source,
            duration=self.averageRuntime or 0,
            image_sm_url=self.image.medium if self.image else None,
            image_lg_url=self.image.original if self.image else None,
            imdb_id=self.externals.imdb if self.externals else None,
            thetvdb_id=self.externals.thetvdb if self.externals else None,
            seasons=with_episodes.to_episode_models(),
        )


# Search results models


class TVmazeSearchResultShow(BaseModel):
    """
    Encapsulates a single show representation in TVmaze search results.
    """

    id: int
    name: str
    genres: list[str] | None
    premiered: datetime.date | None
    ended: datetime.date | None
    network: TVmazeNetwork | None
    webChannel: TVmazeWebChannel | None
    image: TVmazeImage | None
    summary: str | None


class TVmazeSearchResult(BaseModel):
    """Top level DTO encapsulating a search result. TVmaze results are given as
    an array of objects that contain a `score` (which we ignore) and a `show`.
    See class method for handling of the array.
    """

    show: TVmazeSearchResultShow

    def to_search_result_model(self) -> SearchResult:
        sanitized_summary_html = None
        if self.show.summary:
            sanitized_summary_html = sanitize_html(self.show.summary)

        return SearchResult(
            tvmaze_id=self.show.id,
            name=self.show.name,
            genres=self.show.genres,
            start_year=self.show.premiered.year if self.show.premiered else None,
            end_year=self.show.ended.year if self.show.ended else None,
            network=self.show.network.name if self.show.network else None,
            network_country=(
                self.show.network.country.name
                if self.show.network and self.show.network.country
                else None
            ),
            streaming_service=(
                self.show.webChannel.name if self.show.webChannel else None
            ),
            streaming_service_country=(
                self.show.webChannel.country.name
                if self.show.webChannel and self.show.webChannel.country
                else None
            ),
            summary_html=sanitized_summary_html,
            image_sm_url=self.show.image.medium if self.show.image else None,
            image_lg_url=self.show.image.original if self.show.image else None,
        )

    @classmethod
    def to_search_results_model(cls, result_dtos: list[Self]) -> SearchResults:
        return SearchResults(
            results=[dto.to_search_result_model() for dto in result_dtos]
        )
