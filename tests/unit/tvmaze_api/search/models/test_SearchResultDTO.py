import datetime
import pytest

from pydantic import HttpUrl, ValidationError

from tvmaze_api.dtos import TVmazeNetworkDTO, TVmazeCountryDTO, TVmazeImageDTO
from tvmaze_api.search.dtos import TVmazeSearchResultDTO
from ..sample_tvmaze_results.reader import read_sample


def test_response_validation():
    response_json = read_sample("result.json")
    r = TVmazeSearchResultDTO.model_validate_json(response_json)

    assert r.show
    show = r.show

    assert show.id == 166

    assert show.name == "Battlestar Galactica"
    assert show.genres == ["Drama", "Science-Fiction", "War"]
    assert show.premiered == datetime.date(2003, 12, 8)
    assert show.ended == datetime.date(2009, 10, 27)
    assert show.network == TVmazeNetworkDTO(
        name="Syfy", country=TVmazeCountryDTO(name="United States")
    )
    assert show.webChannel is None
    assert show.image == TVmazeImageDTO(
        medium=HttpUrl(
            "https://static.tvmaze.com/uploads/images/medium_portrait/0/2313.jpg"
        )
    )
    assert show.summary == "<p>Summary 1 truncated</p>"


def test_response_validation_failure():
    with pytest.raises(ValidationError):
        response_json = read_sample("result_invalid.json")
        _ = TVmazeSearchResultDTO.model_validate_json(response_json)
