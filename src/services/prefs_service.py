from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import DbUserPrefs
from db.repositories import DbUserPrefsRepository
from models.prefs import UserPrefs


class PrefsService:
    def __init__(self, db_session: AsyncSession, user_id: UUID):
        self.db_session = db_session
        self.user_id = user_id

    async def get_prefs(self) -> UserPrefs:
        """Fetches the user's preferences record, creating it if necessary"""

        repo = DbUserPrefsRepository(session=self.db_session)
        db_prefs = await repo.get_one_or_none(user_id=self.user_id)
        if db_prefs:
            return db_prefs.to_user_prefs_model()

        # User has no prefs record; create it
        try:
            db_prefs = await repo.add(
                DbUserPrefs.from_user_prefs_model(UserPrefs(), self.user_id),
                auto_commit=True,
            )
            return db_prefs.to_user_prefs_model()
        except IntegrityError:
            # Record was created concurrently
            return (await repo.get_one(user_id=self.user_id)).to_user_prefs_model()

    async def update_prefs(self, prefs: UserPrefs) -> None:
        repo = DbUserPrefsRepository(session=self.db_session)
        await repo.upsert(
            DbUserPrefs.from_user_prefs_model(prefs, self.user_id), auto_commit=True
        )
