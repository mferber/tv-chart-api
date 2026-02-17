# run from src as python -m scripts.seed_db

import asyncio

from advanced_alchemy.base import AdvancedDeclarativeBase
from litestar_users.password import PasswordManager
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

import app_config
from db.models import DbShow
from setup.litestar_users.models import User

password_manager = PasswordManager()


def create_users(db_session: AsyncSession) -> list[User]:
    user = User(
        email="test@example.com",
        password_hash=password_manager.hash("password"),
        is_active=True,
        is_verified=True,
    )
    user2 = User(
        email="test2@example.com",
        password_hash=password_manager.hash("password2"),
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    db_session.add(user2)
    return [user, user2]


def create_shows(db_session: AsyncSession, owning_user: User) -> None:
    def make_episode(index: int, special: bool, watched: bool) -> dict:
        return {
            "type": "special" if special else "episode",
            "watched": watched,
        }

    pluribus_seasons = [
        {
            "episodes": [make_episode(i, False, i < 8) for i in range(0, 9)],
        }
    ]

    pluribus = DbShow(
        user_id=owning_user.id,
        tvmaze_id=86175,
        title="Pluribus",
        source="Apple TV",
        duration=60,
        seasons=pluribus_seasons,
    )
    db_session.add(pluribus)

    def all_creatures_season(sn: int) -> dict:
        return {
            "episodes": [
                make_episode(index=i, special=(i == 6), watched=sn <= 2)
                for i in range(0, 7)
            ],
        }

    all_creatures_seasons = [all_creatures_season(s) for s in range(1, 5)]

    all_creatures = DbShow(
        user_id=owning_user.id,
        tvmaze_id=42836,
        title="All Creatures Great & Small",
        source="PBS",
        duration=60,
        seasons=all_creatures_seasons,
    )
    db_session.add(all_creatures)


async def main() -> None:
    app_config.load()
    engine = create_async_engine(app_config.get_db_url())

    async with engine.begin() as conn:
        await conn.run_sync(AdvancedDeclarativeBase.metadata.create_all)

    async with AsyncSession(engine) as db_session:
        try:
            await db_session.execute(delete(DbShow))
            await db_session.execute(delete(User))

            users = create_users(db_session)
            await db_session.flush()  # get user ids

            create_shows(db_session, users[0])

            await db_session.commit()

            print("Database records created")
        except Exception as e:
            print("Database record creation failed:", e)


asyncio.run(main())
