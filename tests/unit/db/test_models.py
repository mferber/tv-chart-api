import uuid

from db.models import EpisodeInfo, SeasonInfo, Show


def test_show_as_text_representation() -> None:
    show = Show(
        owner_id=uuid.uuid4(),
        title="Pluribus",
        source="Apple TV",
        duration=60,
        seasons=[
            SeasonInfo(
                number=1,
                episodes=[
                    EpisodeInfo(season=1, index=0, type="episode", watched=True),
                    EpisodeInfo(season=1, index=1, type="episode", watched=False),
                    EpisodeInfo(season=1, index=2, type="episode", watched=False),
                    EpisodeInfo(season=1, index=3, type="special", watched=False),
                ],
            )
        ],
    )
    text_repr = show.as_text()

    assert "Pluribus" in text_repr
    assert "Apple TV" in text_repr
    assert "60 min." in text_repr
    assert "X..s" in text_repr
