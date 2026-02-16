import datetime
import uuid

from db.models import DbShow


def test_show_as_text_representation() -> None:
    show = DbShow(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now(),
        title="Pluribus",
        source="Apple TV",
        duration=60,
        seasons=[
            {
                "episodes": [
                    {"type": "episode", "watched": True},
                    {"type": "episode", "watched": False},
                    {"type": "episode", "watched": False},
                    {"type": "special", "watched": False},
                ],
            }
        ],
    )
    text_repr = show.as_text()

    assert "Pluribus" in text_repr
    assert "Apple TV" in text_repr
    assert "60 min." in text_repr
    assert "X..s" in text_repr
