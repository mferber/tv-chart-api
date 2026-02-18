from uuid import uuid4

from pydantic import HttpUrl

from db.models import DbShow
from models.show import EpisodeDescriptor, EpisodeType, Show, ShowCreate


def test_domain_show_to_db_show_conversion() -> None:
    show = Show(
        id=uuid4(),
        tvmaze_id=1,
        title="Fictional Show",
        source="PBS",
        duration=60,
        image_sm_url=HttpUrl("http://images.com/small"),
        image_lg_url=HttpUrl("http://images.com/large"),
        seasons=[
            [
                EpisodeDescriptor(EpisodeType.EPISODE, True),
                EpisodeDescriptor(EpisodeType.SPECIAL, False),
            ]
        ],
    )

    user_id = uuid4()
    db_show = DbShow.from_show_model(show, owner_id=user_id)

    assert db_show.id == show.id
    assert db_show.user_id == user_id
    assert db_show.tvmaze_id == show.tvmaze_id
    assert db_show.title == show.title
    assert db_show.source == show.source
    assert db_show.duration == show.duration
    assert db_show.image_sm_url == str(show.image_sm_url)
    assert db_show.image_lg_url == str(show.image_lg_url)
    assert db_show.seasons == [
        [{"type": "episode", "watched": True}, {"type": "special", "watched": False}]
    ]


def test_domain_show_create_to_db_show_conversion() -> None:
    show = ShowCreate(
        tvmaze_id=1,
        title="Fictional Show",
        source="PBS",
        duration=60,
        image_sm_url=HttpUrl("http://images.com/small"),
        image_lg_url=HttpUrl("http://images.com/large"),
        seasons=[
            [
                EpisodeDescriptor(EpisodeType.EPISODE, True),
                EpisodeDescriptor(EpisodeType.SPECIAL, False),
            ]
        ],
    )
    user_id = uuid4()
    db_show = DbShow.from_show_model(show, owner_id=user_id)

    assert db_show.id is None
    assert db_show.user_id == user_id
    assert db_show.tvmaze_id == show.tvmaze_id
    assert db_show.title == show.title
    assert db_show.source == show.source
    assert db_show.duration == show.duration
    assert db_show.image_sm_url == str(show.image_sm_url)
    assert db_show.image_lg_url == str(show.image_lg_url)
    assert db_show.seasons == [
        [{"type": "episode", "watched": True}, {"type": "special", "watched": False}]
    ]


def test_db_show_to_show_conversion() -> None:
    db_show = DbShow(
        id=uuid4(),
        user_id=uuid4(),
        tvmaze_id=1,
        title="Fictional Show",
        source="PBS",
        duration=60,
        image_sm_url="http://images.com/small",
        image_lg_url="http://images.com/large",
        seasons=[
            [
                {"type": "episode", "watched": True},
                {"type": "special", "watched": False},
            ]
        ],
    )

    show = db_show.to_show_model()

    assert show.id == db_show.id
    assert show.tvmaze_id == db_show.tvmaze_id
    assert show.title == db_show.title
    assert show.source == db_show.source
    assert show.duration == db_show.duration
    assert show.image_sm_url == HttpUrl(db_show.image_sm_url)
    assert show.image_lg_url == HttpUrl(db_show.image_lg_url)
    assert show.seasons == [
        [
            EpisodeDescriptor(EpisodeType.EPISODE, True),
            EpisodeDescriptor(EpisodeType.SPECIAL, False),
        ]
    ]
