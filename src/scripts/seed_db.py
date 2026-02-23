# run from src as python -m scripts.seed_db

import asyncio

from advanced_alchemy.base import AdvancedDeclarativeBase
from litestar_users.password import PasswordManager
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

import app_config
from db.models import DbShow
from litestar_users_setup.models import User

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
        [make_episode(i, False, i < 8) for i in range(0, 9)],
    ]

    pluribus = DbShow(
        user_id=owning_user.id,
        tvmaze_id=86175,
        title="Pluribus",
        source="Apple TV",
        duration=60,
        image_sm_url="https://static.tvmaze.com/uploads/images/medium_portrait/592/1481086.jpg",
        image_lg_url="https://static.tvmaze.com/uploads/images/original_untouched/592/1481086.jpg",
        imdb_id="tt22202452",
        thetvdb_id=436457,
        seasons=pluribus_seasons,
    )
    db_session.add(pluribus)

    def all_creatures_season(sn: int) -> list[dict]:
        return [
            make_episode(index=i, special=(i == 6), watched=sn <= 2)
            for i in range(0, 7)
        ]

    all_creatures_seasons = [all_creatures_season(s) for s in range(1, 5)]

    all_creatures = DbShow(
        user_id=owning_user.id,
        tvmaze_id=42836,
        title="All Creatures Great & Small",
        source="PBS",
        duration=60,
        image_sm_url="https://static.tvmaze.com/uploads/images/medium_portrait/593/1483974.jpg",
        image_lg_url="https://static.tvmaze.com/uploads/images/original_untouched/593/1483974.jpg",
        thetvdb_id=378982,
        imdb_id="tt10590066",
        seasons=all_creatures_seasons,
    )
    db_session.add(all_creatures)

    the_americans_seasons = [
        [make_episode(i, False, i < 8) for i in range(0, 9)],
    ]

    the_americans = DbShow(
        user_id=owning_user.id,
        tvmaze_id=157,
        title="The Americans",
        source="FX",
        duration=60,
        image_sm_url="https://static.tvmaze.com/uploads/images/medium_portrait/146/366911.jpg",
        image_lg_url="https://static.tvmaze.com/uploads/images/original_untouched/146/366911.jpg",
        thetvdb_id=261690,
        imdb_id="tt2149175",
        seasons=the_americans_seasons,
    )

    db_session.add(the_americans)


async def main() -> None:
    app_config.load()
    engine = create_async_engine(app_config.get_db_url())

    async with engine.begin() as conn:
        await conn.run_sync(AdvancedDeclarativeBase.metadata.drop_all)
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
