from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from db.models import DbShow
from db.repositories import DbShowRepository
from models.show import Show


class ShowService:
    async def get_shows(self, db_session: AsyncSession, user_id: UUID) -> list[Show]:
        repository = DbShowRepository(session=db_session)
        db_shows = await repository.list(DbShow.user_id == user_id)
        return [db_show.to_show_model() for db_show in db_shows]
