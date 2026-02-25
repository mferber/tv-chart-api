import pytest
from pydantic import HttpUrl, ValidationError

from tvmaze_api.models import (
    TVmazeCountry,
    TVmazeEpisodeList,
    TVmazeNetwork,
    TVmazeShow,
    TVmazeWebChannel,
)

from ..sample_tvmaze_show_responses.reader import read_sample


def test_valid_network_show() -> None:
    json = read_sample("network_show.json")

    tvmaze_show = TVmazeShow.model_validate_json(json)

    assert tvmaze_show.id == 6456
    assert tvmaze_show.name == "Counterpart"
    assert tvmaze_show.averageRuntime == 60
    assert tvmaze_show.network == TVmazeNetwork(
        name="STARZ", country=TVmazeCountry(name="United States")
    )
    assert tvmaze_show.webChannel is None
    assert tvmaze_show.image.medium == HttpUrl(
        "https://static.tvmaze.com/uploads/images/medium_portrait/175/438213.jpg"
    )
    assert tvmaze_show.image.original == HttpUrl(
        "https://static.tvmaze.com/uploads/images/original_untouched/175/438213.jpg"
    )


def test_valid_streaming_show() -> None:
    json = read_sample("streaming_service_show.json")

    tvmaze_show = TVmazeShow.model_validate_json(json)

    assert tvmaze_show.id == 64860
    assert tvmaze_show.name == "Colin From Accounts"
    assert tvmaze_show.webChannel == TVmazeWebChannel(
        name="Binge", country=TVmazeCountry(name="Australia")
    )


def test_invalid_show_fails() -> None:
    json = read_sample("invalid.json")

    with pytest.raises(ValidationError):
        _ = TVmazeShow.model_validate_json(json)


def test_valid_episode_list() -> None:
    json = read_sample("episodes.json")

    episode_list = TVmazeEpisodeList.model_validate_json(json)
    episodes = episode_list.root

    assert len(episodes) == 254  # yeah, modern Doctor Who has a lot of episodes

    # spot check an episode
    rose = episodes[0]
    assert rose.id == 13857
    assert rose.name == "Rose"
    assert rose.season == 1
    assert rose.number == 1
    assert rose.type == "regular"
    assert rose.airdate == "2005-03-26"
    assert rose.runtime == 45
    assert rose.summary and "Rose Tyler meets a mysterious stranger" in rose.summary

    # spot check a special
    xmas_invasion = next(filter(lambda ep: ep.id == 13961, episodes))
    assert xmas_invasion.name == "The Christmas Invasion"
    assert xmas_invasion.type == "significant_special"
    assert xmas_invasion.season == 1
    assert xmas_invasion.number is None

    # spot check an episode with no summary
    asylum_prequel = next(filter(lambda ep: ep.id == 332914, episodes))
    assert asylum_prequel.name == "Prequel (Asylum of the Daleks)"
    assert asylum_prequel.summary is None

    # spot check an insignificant special
    # (these will be ignored by the app)
    pond_life = next(filter(lambda ep: ep.id == 13997, episodes))
    assert pond_life.name == "Pond Life: Episode One – April"
    assert pond_life.type == "insignificant_special"
    assert pond_life.season == 7
    assert pond_life.number is None


def test_invalid_episodes_fails() -> None:
    json = read_sample("invalid_episodes.json")

    with pytest.raises(ValidationError):
        _ = TVmazeShow.model_validate_json(json)
