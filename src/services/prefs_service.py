from uuid import UUID

from advanced_alchemy.exceptions import NotFoundError
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import DbUserPrefs
from db.repositories import DbUserPrefsRepository
from models.prefs import UserPrefs


class PrefsService:
    def __init__(self, db_session: AsyncSession, user_id: UUID):
        self.db_session = db_session
        self.user_id = user_id

    async def get_prefs(self) -> UserPrefs:
        repo = DbUserPrefsRepository(session=self.db_session)

        try:
            return (await repo.get_one(user_id=self.user_id)).to_user_prefs_model()
        except NotFoundError:
            # User has no prefs record for some reason; recreate it
            db_prefs = await repo.upsert(
                DbUserPrefs.from_user_prefs_model(UserPrefs(), self.user_id),
                auto_commit=True,
            )
            return db_prefs.to_user_prefs_model()

    async def update_prefs(self, prefs: UserPrefs) -> None:
        repo = DbUserPrefsRepository(session=self.db_session)
        await repo.upsert(
            DbUserPrefs.from_user_prefs_model(prefs, self.user_id), auto_commit=True
        )
