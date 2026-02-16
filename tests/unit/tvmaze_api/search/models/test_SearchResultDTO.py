import datetime

import pydantic
import pytest
from pydantic import HttpUrl

from tvmaze_api.dtos.common_dtos import (
    TVmazeCountryDTO,
    TVmazeImageDTO,
    TVmazeNetworkDTO,
)
from tvmaze_api.dtos.search_dtos import TVmazeSearchResultDTO

from ..sample_tvmaze_results.reader import read_sample


def test_response_validation() -> None:
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
        ),
        original=HttpUrl(
            "https://static.tvmaze.com/uploads/images/original_untouched/0/2313.jpg"
        ),
    )
    assert show.summary == "<p>Summary 1 truncated</p>"


def test_response_validation_failure() -> None:
    with pytest.raises(pydantic.ValidationError):
        response_json = read_sample("result_invalid.json")
        _ = TVmazeSearchResultDTO.model_validate_json(response_json)
