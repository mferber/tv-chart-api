# run from src as python -m scripts.seed_db

import asyncio

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
    def make_episode(
        index: int, special: bool, displayNumber: int | None, watched: bool
    ) -> dict:
        return {
            "title": f"Episode index {index} title",
            "type": "special" if special else "episode",
            "displayNumber": displayNumber,
            "watched": watched,
        }

    # Pluribus

    pluribus_seasons = [
        [make_episode(i, False, i + 1, i < 8) for i in range(0, 9)],
    ]

    pluribus = DbShow(
        user_id=owning_user.id,
        tvmaze_id=86175,
        title="Pluribus",
        favorite=True,
        source="Apple TV",
        duration=60,
        image_sm_url="https://static.tvmaze.com/uploads/images/medium_portrait/592/1481086.jpg",
        image_lg_url="https://static.tvmaze.com/uploads/images/original_untouched/592/1481086.jpg",
        imdb_id="tt22202452",
        thetvdb_id=436457,
        seasons=pluribus_seasons,
    )
    db_session.add(pluribus)

    # All Creatures Great & Small

    def all_creatures_season(sn: int) -> list[dict]:
        season = []
        next_display_number = 1
        for i in range(0, 7):
            is_special = i == 6
            if is_special:
                displayNumber = None
            else:
                displayNumber = next_display_number
                next_display_number += 1
            season.append(
                make_episode(
                    index=i,
                    special=(i == 6),
                    displayNumber=displayNumber,
                    watched=sn <= 2,
                )
            )
        return season

    all_creatures_seasons = [all_creatures_season(s) for s in range(1, 5)]

    all_creatures = DbShow(
        user_id=owning_user.id,
        tvmaze_id=42836,
        title="All Creatures Great & Small",
        favorite=True,
        source="PBS",
        duration=60,
        image_sm_url="https://static.tvmaze.com/uploads/images/medium_portrait/593/1483974.jpg",
        image_lg_url="https://static.tvmaze.com/uploads/images/original_untouched/593/1483974.jpg",
        thetvdb_id=378982,
        imdb_id="tt10590066",
        seasons=all_creatures_seasons,
    )
    db_session.add(all_creatures)

    # The Americans

    the_americans_seasons = [
        [make_episode(i, False, i + 1, i < 8) for i in range(0, 9)],
    ]

    the_americans = DbShow(
        user_id=owning_user.id,
        tvmaze_id=157,
        title="The Americans",
        favorite=False,
        source="FX",
        duration=60,
        image_sm_url="https://static.tvmaze.com/uploads/images/medium_portrait/146/366911.jpg",
        image_lg_url="https://static.tvmaze.com/uploads/images/original_untouched/146/366911.jpg",
        thetvdb_id=261690,
        imdb_id="tt2149175",
        seasons=the_americans_seasons,
    )

    db_session.add(the_americans)

    # BoJack Horseman

    bojack_seasons = [
        [
            make_episode(i, i < 12, i + 1 if i < 12 else None, True)
            for i in range(0, 13)
        ],
        [make_episode(i, i < 11, i + 1, True) for i in range(0, 12)],
        [make_episode(i, i < 11, i + 1, True) for i in range(0, 12)],
        [make_episode(i, i < 11, i + 1, i < 2) for i in range(0, 12)],
        [make_episode(i, i < 11, i + 1, False) for i in range(0, 12)],
        [make_episode(i, i < 11, i + 1, False) for i in range(0, 16)],
    ]

    bojack = DbShow(
        user_id=owning_user.id,
        tvmaze_id=184,
        title="BoJack Horseman",
        favorite=True,
        source="Netflix",
        duration=30,
        image_sm_url="https://static.tvmaze.com/uploads/images/medium_portrait/405/1012627.jpg",
        image_lg_url="https://static.tvmaze.com/uploads/images/original_untouched/405/1012627.jpg",
        thetvdb_id=282254,
        imdb_id="tt3398228",
        seasons=bojack_seasons,
    )
    db_session.add(bojack)


async def main() -> None:
    app_config.load()
    engine = create_async_engine(app_config.get_db_url())

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
