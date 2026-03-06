"""
Models for TVmaze API responses.
"""

import datetime

from pydantic import BaseModel, HttpUrl, RootModel

from models.search import SearchResult, SearchResults
from models.show import EpisodeDescriptor, EpisodeDetails, EpisodeType, ShowCreate
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

    def to_episode_descriptor_model(
        self, displayNumber: int | None
    ) -> EpisodeDescriptor:
        episode_type = (
            EpisodeType.EPISODE if self.type == "regular" else EpisodeType.SPECIAL
        )
        return EpisodeDescriptor(
            title=self.name,
            type=episode_type,
            displayNumber=displayNumber,
            watched=False,
        )

    def to_episode_details_model(self) -> EpisodeDetails:
        episode_type = (
            EpisodeType.EPISODE if self.type == "regular" else EpisodeType.SPECIAL
        )

        release_date: datetime.date | None = None
        try:
            release_date = (
                datetime.date.fromisoformat(self.airdate) if self.airdate else None
            )
        except ValueError:
            pass

        return EpisodeDetails(
            title=self.name,
            type=episode_type,
            duration=self.runtime,
            release_date=release_date,
            summary=sanitize_html(self.summary) if self.summary else None,
        )


class TVmazeEpisodeList(RootModel):
    root: list[TVmazeEpisode]

    def to_episode_descriptor_models(self) -> list[list[EpisodeDescriptor]]:
        filtered_eps = filter(lambda ep: ep.type != "insignificant_special", self.root)

        seasons: list[list[EpisodeDescriptor]] = []
        current_season: list[EpisodeDescriptor] = []
        current_season_num = 1
        next_episode_number = 1
        for ep in filtered_eps:
            while ep.season != current_season_num:
                seasons.append(current_season)
                current_season = []
                current_season_num += 1
                next_episode_number = 1
            if ep.type == "regular":
                actual_next_episode_number = next_episode_number
                next_episode_number += 1
            else:
                actual_next_episode_number = None
            current_season.append(
                ep.to_episode_descriptor_model(actual_next_episode_number)
            )
        if current_season:
            seasons.append(current_season)
        return seasons

    def to_episode_details_models(self) -> list[list[EpisodeDetails]]:
        filtered_eps = filter(lambda ep: ep.type != "insignificant_special", self.root)

        seasons: list[list[EpisodeDetails]] = []
        current_season: list[EpisodeDetails] = []
        current_season_num = 1
        for ep in filtered_eps:
            while ep.season != current_season_num:
                seasons.append(current_season)
                current_season = []
                current_season_num += 1

            current_season.append(ep.to_episode_details_model())

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

    def to_show_create_model(
        self, *, with_episodes: list[list[EpisodeDescriptor]]
    ) -> ShowCreate:
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
            seasons=with_episodes,
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


class TVmazeSearchResultList(RootModel):
    root: list[TVmazeSearchResult]

    def to_search_results_model(self) -> SearchResults:
        return SearchResults(
            results=[result.to_search_result_model() for result in self.root]
        )
