import datetime

import pydantic
import pytest
from helpers.testing_data.mock_responses.reader import SampleFileReader
from pydantic import HttpUrl

from tvmaze_api.models import (
    TVmazeCountry,
    TVmazeImage,
    TVmazeNetwork,
    TVmazeSearchResult,
)

sample_file_reader = SampleFileReader("sample_tvmaze_search_results")


def test_response_validation() -> None:
    response_json = sample_file_reader.read("result.json")
    r = TVmazeSearchResult.model_validate_json(response_json)

    assert r.show
    show = r.show

    assert show.id == 166

    assert show.name == "Battlestar Galactica"
    assert show.genres == ["Drama", "Science-Fiction", "War"]
    assert show.premiered == datetime.date(2003, 12, 8)
    assert show.ended == datetime.date(2009, 10, 27)
    assert show.network == TVmazeNetwork(
        name="Syfy", country=TVmazeCountry(name="United States")
    )
    assert show.webChannel is None
    assert show.image == TVmazeImage(
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
        response_json = sample_file_reader.read("result_invalid.json")
        _ = TVmazeSearchResult.model_validate_json(response_json)
