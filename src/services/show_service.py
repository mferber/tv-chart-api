from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from db.models import DbShow
from db.repositories import DbShowRepository
from models.show import Show, ShowCreate


class ShowService:
    async def get_shows(self, db_session: AsyncSession, user_id: UUID) -> list[Show]:
        repository = DbShowRepository(session=db_session)
        db_shows = await repository.list(DbShow.user_id == user_id)
        return [db_show.to_show_model() for db_show in db_shows]

    async def add_show(
        self, show: ShowCreate, db_session: AsyncSession, user_id: UUID
    ) -> Show:
        repository = DbShowRepository(session=db_session)
        db_show = await repository.add(
            DbShow.from_show_model(show, owner_id=user_id), auto_commit=True
        )
        return db_show.to_show_model()
