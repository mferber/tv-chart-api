from uuid import UUID

import advanced_alchemy.exceptions
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import DbShow
from db.repositories import DbShowRepository
from models.show import Show, ShowCreate


class ShowServiceError(Exception):
    pass


class ShowNotFound(ShowServiceError):
    pass


class EpisodeNotFound(ShowServiceError):
    def __init__(self, season: int, episode_index: int):
        self.season = season
        self.episode_index = episode_index
        super().__init__()


class ShowService:
    def __init__(self, db_session: AsyncSession, user_id: UUID):
        self.db_session = db_session
        self.user_id = user_id

    async def get_shows(self) -> dict[UUID, Show]:
        repository = DbShowRepository(session=self.db_session)
        db_shows = await repository.list(DbShow.user_id == self.user_id)
        return {db_show.id: db_show.to_show_model() for db_show in db_shows}

    async def get_show(self, show_id: UUID) -> Show:
        repository = DbShowRepository(session=self.db_session)
        try:
            db_show = await repository.get_one(
                DbShow.user_id == self.user_id, DbShow.id == show_id
            )
            return db_show.to_show_model()
        except advanced_alchemy.exceptions.NotFoundError:
            raise ShowNotFound()

    async def add_show(self, show: ShowCreate) -> Show:
        repository = DbShowRepository(session=self.db_session)
        db_show = await repository.add(
            DbShow.from_show_model(show, owner_id=self.user_id), auto_commit=True
        )
        return db_show.to_show_model()

    async def delete_show(self, show_id: UUID) -> None:
        repository = DbShowRepository(session=self.db_session)
        deleted = await repository.delete_where(
            DbShow.user_id == self.user_id, DbShow.id == show_id, auto_commit=True
        )
        if not deleted:
            raise ShowNotFound()

    async def mark_episodes(
        self, show_id: UUID, episode_indices: list[tuple[int, int]], watched: bool
    ) -> Show:
        shows = await self.get_shows()
        show = shows[show_id]

        # validate requested episodes before making any changes
        for season_idx, ep_idx in episode_indices:
            try:
                show.seasons[season_idx][ep_idx]
            except IndexError:
                raise EpisodeNotFound(season=season_idx + 1, episode_index=ep_idx)

        for season_idx, ep_idx in episode_indices:
            show.seasons[season_idx][ep_idx].watched = watched

        repository = DbShowRepository(session=self.db_session)
        updated_db_show = await repository.update(
            DbShow.from_show_model(show, owner_id=self.user_id), auto_commit=True
        )
        return updated_db_show.to_show_model()
