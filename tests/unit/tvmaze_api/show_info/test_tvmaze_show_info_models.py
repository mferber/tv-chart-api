import datetime

import pytest
from helpers.testing_data.mock_responses.reader import SampleFileReader
from pydantic import HttpUrl, ValidationError

from models.show import EpisodeType
from tvmaze_api.models import (
    TVmazeCountry,
    TVmazeEpisode,
    TVmazeEpisodeList,
    TVmazeNetwork,
    TVmazeShow,
    TVmazeWebChannel,
)

sample_file_reader = SampleFileReader("sample_tvmaze_show_responses")


def test_valid_network_show() -> None:
    """Tests that a normal show from a network deserializes correctly"""

    json = sample_file_reader.read("network_show.json")

    tvmaze_show = TVmazeShow.model_validate_json(json)

    assert tvmaze_show.id == 6456
    assert tvmaze_show.name == "Counterpart"
    assert tvmaze_show.averageRuntime == 60
    assert tvmaze_show.network == TVmazeNetwork(
        name="STARZ", country=TVmazeCountry(name="United States")
    )
    assert tvmaze_show.webChannel is None
    assert tvmaze_show.image is not None
    assert tvmaze_show.image.medium == HttpUrl(
        "https://static.tvmaze.com/uploads/images/medium_portrait/175/438213.jpg"
    )
    assert tvmaze_show.image.original == HttpUrl(
        "https://static.tvmaze.com/uploads/images/original_untouched/175/438213.jpg"
    )
    assert tvmaze_show.externals is not None
    assert tvmaze_show.externals.imdb == "tt4643084"
    assert tvmaze_show.externals.thetvdb == 337302


def test_valid_streaming_show() -> None:
    """Tests that a normal show from a streaming service deserializes correctly"""

    json = sample_file_reader.read("streaming_service_show.json")

    tvmaze_show = TVmazeShow.model_validate_json(json)

    assert tvmaze_show.id == 64860
    assert tvmaze_show.name == "Colin From Accounts"
    assert tvmaze_show.webChannel == TVmazeWebChannel(
        name="Binge", country=TVmazeCountry(name="Australia")
    )
    assert tvmaze_show.externals is not None
    assert tvmaze_show.externals.imdb == "tt18228732"
    assert tvmaze_show.externals.thetvdb == 421974


def test_invalid_show_fails() -> None:
    """Tests that invalid JSON for a show fails deserialization"""

    json = sample_file_reader.read("network_show_invalid.json")

    with pytest.raises(ValidationError):
        _ = TVmazeShow.model_validate_json(json)


def test_valid_episode_list() -> None:
    """Tests that an episode list deserializes correctly"""

    json = sample_file_reader.read("complicated_show_episodes.json")

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
    """Tests that invalid JSON for episode list fails deserialization"""

    json = sample_file_reader.read("invalid_episodes.json")

    with pytest.raises(ValidationError):
        _ = TVmazeShow.model_validate_json(json)


def test_tvmaze_show_to_show_create_model_conversion() -> None:
    """Tests that a TVmaze show validates into a ShowCreate model"""

    tvmaze_show = TVmazeShow.model_validate_json(
        sample_file_reader.read("network_show.json")
    )
    tvmaze_episode_list = TVmazeEpisodeList.model_validate_json(
        sample_file_reader.read("network_show_episodes.json")
    )

    episodes = tvmaze_episode_list.to_episode_descriptor_models()
    show_create = tvmaze_show.to_show_create_model(with_episodes=episodes)

    assert show_create.tvmaze_id == 6456
    assert show_create.title == "Counterpart"
    assert show_create.source == "STARZ"
    assert show_create.duration == 60
    assert show_create.image_sm_url == HttpUrl(
        "https://static.tvmaze.com/uploads/images/medium_portrait/175/438213.jpg"
    )
    assert show_create.image_lg_url == HttpUrl(
        "https://static.tvmaze.com/uploads/images/original_untouched/175/438213.jpg"
    )
    assert show_create.imdb_id == "tt4643084"
    assert show_create.thetvdb_id == 337302
    assert len(show_create.seasons) == 2
    assert len(show_create.seasons[0]) == 10
    assert len(show_create.seasons[1]) == 10
    for season in show_create.seasons:
        assert all(episode.type == EpisodeType.EPISODE for episode in season)
        assert all(not episode.watched for episode in season)


def test_tvmaze_episode_to_episode_descriptor_model_conversion() -> None:
    """Tests that a TVmaze episode validates into an EpisodeDescriptor model"""

    tvmaze_episode = TVmazeEpisode(
        id=1,
        name="Episode Title",
        season=1,
        number=1,
        type="regular",
        airdate="2026-01-01",
        runtime=60,
        summary="Episode summary",
    )

    episode = tvmaze_episode.to_episode_descriptor_model(displayNumber=1)

    assert episode.title == "Episode Title"
    assert episode.type == EpisodeType.EPISODE
    assert episode.displayNumber == 1
    assert not episode.watched


def test_tvmaze_episodes_to_episode_descriptors_model_conversion() -> None:
    """Tests that a flat TVmaze episode list validates into a structured list of
    EpisodeDescriptors in seasons"""

    tvmaze_episode_list = TVmazeEpisodeList.model_validate_json(
        sample_file_reader.read("network_show_episodes.json")
    )

    results = tvmaze_episode_list.to_episode_descriptor_models()

    assert len(results) == 2
    assert len(results[0]) == 10
    assert len(results[1]) == 10

    assert all(ep.type == EpisodeType.EPISODE for ep in results[0])
    assert all(ep.type == EpisodeType.EPISODE for ep in results[1])
    assert all(not ep.watched for ep in results[0])
    assert all(not ep.watched for ep in results[1])


def test_tvmaze_episodes_to_episode_descriptors_model_conversion_skips_missing_season() -> (
    None
):
    """Tests that a missing season in TVmaze episode list validates into an empty season in
    structured list of EpisodeDescriptors"""

    tvmaze_episode_list = TVmazeEpisodeList.model_validate_json(
        sample_file_reader.read("network_show_episodes_skip_season.json")
    )

    results = tvmaze_episode_list.to_episode_descriptor_models()

    assert len(results) == 3
    assert len(results[0]) == 2
    assert len(results[1]) == 0
    assert len(results[2]) == 2
    assert all(ep.type == EpisodeType.EPISODE for ep in results[0])
    assert all(ep.type == EpisodeType.EPISODE for ep in results[2])


def test_tvmaze_episode_to_episode_detail_model_conversion() -> None:
    """Tests that a TVmaze episode validates into an EpisodeDetails model"""

    tvmaze_episode = TVmazeEpisode(
        id=1,
        name="Episode Title",
        season=1,
        number=1,
        type="regular",
        airdate="2026-01-01",
        runtime=60,
        summary="Episode summary",
    )

    episode = tvmaze_episode.to_episode_details_model()

    assert episode.title == "Episode Title"
    assert episode.type == EpisodeType.EPISODE
    assert episode.duration == 60
    assert episode.release_date == datetime.date(2026, 1, 1)
    assert episode.summary == "Episode summary"


def test_tvmaze_episode_to_episode_detail_model_conversion_with_missing_or_invalid_data() -> (
    None
):
    """Tests that a TVmaze episode validates into an EpisodeDetails model with None for
    missing or invalid data"""

    tvmaze_episode = TVmazeEpisode(
        id=1,
        name=None,
        season=1,
        number=None,
        type="special",
        airdate="not a date",
        runtime=None,
        summary=None,
    )

    episode = tvmaze_episode.to_episode_details_model()

    assert episode.title is None
    assert episode.type == EpisodeType.SPECIAL
    assert episode.duration is None
    assert episode.release_date is None
    assert episode.summary is None


def test_tvmaze_episode_to_episode_detail_model_conversion_sanitizes_summary() -> None:
    """Tests that episode summary is sanitized when validating into an EpisodeDetails model"""

    tvmaze_episode = TVmazeEpisode(
        id=1,
        name="Episode Title",
        season=1,
        number=1,
        type="regular",
        airdate="2026-01-01",
        runtime=60,
        summary='<p>Paragraph 1<script>document.write(\'this is a major security flaw!\')</script></p><p>Paragraph 2 <a href="https://dangerous.site.com/">link text</a></p><p>Paragraph 3 <b><i>bold + italic</i></b> plain <span style="font-weight: bold">bold css</span> <span style="font-style: italic">italic css</span> <span style="margin: 10px">margin css</span></p><p>Paragraph 4 <iframe src="https://dangerous.site.com"></iframe></p><p>Paragraph 5 <img src="https://dangerous.site.com"></p><p>Paragraph 6 bare ampersand & more text</p>',
    )

    episode = tvmaze_episode.to_episode_details_model()

    assert (
        episode.summary
        == "<p>Paragraph 1</p><p>Paragraph 2 link text</p><p>Paragraph 3 <strong><em>bold + italic</em></strong> plain <strong>bold css</strong> <em>italic css</em> margin css</p><p>Paragraph 4 </p><p>Paragraph 5 </p><p>Paragraph 6 bare ampersand &amp; more text</p>"
    )


def test_tvmaze_episodes_to_episode_details_model_conversion_skips_missing_season() -> (
    None
):
    """Tests that a missing season in TVmaze episode list validates into an empty season in
    structured list of EpisodeDetails models"""

    tvmaze_episode_list = TVmazeEpisodeList.model_validate_json(
        sample_file_reader.read("network_show_episodes_skip_season.json")
    )

    results = tvmaze_episode_list.to_episode_details_models()

    assert len(results) == 3
    assert len(results[0]) == 2
    assert len(results[1]) == 0
    assert len(results[2]) == 2
    assert all(ep.type == EpisodeType.EPISODE for ep in results[0])
    assert all(ep.type == EpisodeType.EPISODE for ep in results[2])


def test_show_with_complicated_episodes() -> None:
    """Tests against Doctor Who, a long complicated show with lots of specials
    interspersed among the regular episodes"""

    tvmaze_show = TVmazeShow.model_validate_json(
        sample_file_reader.read("complicated_show.json")
    )
    tvmaze_episode_list = TVmazeEpisodeList.model_validate_json(
        sample_file_reader.read("complicated_show_episodes.json")
    )

    show_create = tvmaze_show.to_show_create_model(
        with_episodes=tvmaze_episode_list.to_episode_descriptor_models()
    )

    assert len(show_create.seasons) == 13

    # spot check season 6: it has lots of specials interspersed
    season6 = show_create.seasons[5]
    assert len(season6) == 20
    assert len(list(filter(lambda ep: ep.type == EpisodeType.SPECIAL, season6))) == 7
    assert season6[0].type == EpisodeType.SPECIAL
    assert season6[1].type == EpisodeType.EPISODE
    assert season6[2].type == EpisodeType.EPISODE
    assert season6[3].type == EpisodeType.SPECIAL
