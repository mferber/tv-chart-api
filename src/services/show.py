from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from db.models import DbShow
from db.repositories import DbShowRepository
from models.show import Show, ShowCreate


class ShowServiceError(Exception):
    pass


class ShowNotFound(ShowServiceError):
    pass


class ShowService:
    def __init__(self, db_session: AsyncSession, user_id: UUID):
        self.db_session = db_session
        self.user_id = user_id

    async def get_shows(self) -> list[Show]:
        repository = DbShowRepository(session=self.db_session)
        db_shows = await repository.list(DbShow.user_id == self.user_id)
        return [db_show.to_show_model() for db_show in db_shows]

    async def add_show(self, show: ShowCreate) -> Show:
        repository = DbShowRepository(session=self.db_session)
        db_show = await repository.add(
            DbShow.from_show_model(show, owner_id=self.user_id), auto_commit=True
        )
        return db_show.to_show_model()

    async def delete_show(self, show_id: UUID) -> None:
        repository = DbShowRepository(session=self.db_session)
        deleted = await repository.delete_where(
            DbShow.user_id == self.user_id, DbShow.id == show_id
        )
        if not deleted:
            raise ShowNotFound()
