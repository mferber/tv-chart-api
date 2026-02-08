from collections.abc import Callable
from uuid import UUID

from advanced_alchemy.base import UUIDAuditBase
from litestar_users.password import PasswordManager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from testcontainers.postgres import PostgresContainer  # type: ignore
from unit.common.test_users import test_users

from db.models import Show
from setup.litestar_users.models import User


async def _add_user(db_session: AsyncSession, email: str, password: str) -> UUID:
    """Adds user with given email and password, and returns its UUID"""

    hashed_pw = PasswordManager().hash(password)
    user = User(
        email=email,
        password_hash=hashed_pw,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user.id


async def _add_show(
    db_session: AsyncSession,
    *,
    user_id: UUID,
    title: str,
    tvmaze_id: int,
    source: str,
    duration: int,
    season_lengths: list[int],
    is_special: Callable[[int, int], bool],
    is_watched: Callable[[int, int], bool],
) -> None:
    """Adds a show to the database.

    Args:
        is_special: callback receiving the season number and episode index (0-based); returns
            true if this episode is a special.
        is_watched: similar callback; returns true if this episode should be marked watched.
    """
    seasons = []
    for season_idx, season_length in enumerate(season_lengths):
        season = season_idx + 1
        season_contents = []
        for ep_idx in range(0, season_length):
            season_contents.append(
                {
                    "type": "special" if is_special(season, ep_idx) else "episode",
                    "watched": is_watched(season, ep_idx),
                }
            )
        seasons.append(season_contents)

    db_session.add(
        Show(
            user_id=user_id,
            tvmaze_id=tvmaze_id,
            title=title,
            source=source,
            duration=duration,
            seasons=seasons,
        )
    )
    await db_session.flush()


async def seed_test_db(test_db_container: PostgresContainer) -> None:
    engine = create_async_engine(test_db_container.get_connection_url())
    async with engine.begin() as conn:
        await conn.run_sync(UUIDAuditBase.metadata.create_all)

    async with AsyncSession(engine) as db_session:
        db_user_ids: dict[str, UUID] = {}
        for test_user_id, user_info in test_users.items():
            [email, password] = user_info
            db_user_ids[test_user_id] = await _add_user(db_session, email, password)

        # user 1 is watching "All Creatures Great & Small"
        await _add_show(
            db_session,
            user_id=db_user_ids["test_user1"],
            title="All Creatures Great & Small",
            tvmaze_id=42836,
            source="PBS",
            duration=60,
            season_lengths=[7, 7, 7, 7],
            # final episode of every season is a special
            is_special=lambda season, ep_idx: ep_idx == 6,
            # mark first season as watched
            is_watched=lambda season, ep_idx: season == 1,
        )

        # user 2 has just started "Pluribus"
        await _add_show(
            db_session,
            user_id=db_user_ids["test_user2"],
            title="Pluribus",
            tvmaze_id=86175,
            source="Apple TV",
            duration=60,
            season_lengths=[9],
            is_special=lambda season, ep_idx: False,
            is_watched=lambda season, ep_idx: season == 1 and ep_idx == 0,
        )

        await db_session.commit()
