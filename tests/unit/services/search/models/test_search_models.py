"""Tests for SearchResult and SearchResults models.

Verifies that TVmaze result sets are transformed to domain SearchResults models as
expected.
"""

import pydantic
import pytest

from services.search.models import SearchResult, SearchResults

from .sample_tvmaze_responses.reader import get_TVmaze_response_DTOs_from_json


def test_valid_result_set():
    result_dtos = get_TVmaze_response_DTOs_from_json("multiple_results.json")

    model = SearchResults.from_tvmaze_dto_list(result_dtos)

    assert len(model.results) == 2
    assert model.results[0] == SearchResult(
        tvmaze_id=166,
        name="Battlestar Galactica",
        genres=["Drama", "Science-Fiction", "War"],
        start_year=2003,
        end_year=2009,
        network="Syfy",
        network_country="United States",
        streaming_service=None,
        streaming_service_country=None,
        summary_html="<p>Summary 1 truncated</p>",
        image_url="https://static.tvmaze.com/uploads/images/medium_portrait/0/2313.jpg",
    )
    assert model.results[1] == SearchResult(
        tvmaze_id=1059,
        name="Battlestar Galactica",
        genres=["Action", "Adventure", "Science-Fiction"],
        start_year=1978,
        end_year=1979,
        network="ABC",
        network_country="United States",
        streaming_service=None,
        streaming_service_country=None,
        summary_html="<p>Summary 2 truncated</p>",
        image_url="https://static.tvmaze.com/uploads/images/medium_portrait/6/17017.jpg",
    )


def test_invalid_result_set_fails_validation():
    with pytest.raises(pydantic.ValidationError):
        result_dtos = get_TVmaze_response_DTOs_from_json(
            "multiple_results_invalid.json"
        )

        _ = SearchResults.from_tvmaze_dto_list(result_dtos)


def test_result_with_all_optional_fields_missing():
    result_dtos = get_TVmaze_response_DTOs_from_json("optional_fields_missing.json")

    model = SearchResults.from_tvmaze_dto_list(result_dtos)

    assert len(model.results) == 1
    result = model.results[0]
    assert result.genres is None
    assert result.start_year is None
    assert result.end_year is None
    assert result.network is None
    assert result.network_country is None
    assert result.streaming_service is None
    assert result.streaming_service_country is None
    assert result.summary_html is None
    assert result.image_url is None


def test_result_with_US_network():
    result_dtos = get_TVmaze_response_DTOs_from_json("us_network.json")

    model = SearchResults.from_tvmaze_dto_list(result_dtos)

    assert len(model.results) == 1
    result = model.results[0]
    assert result.network == "Syfy"
    assert result.network_country == "United States"


def test_result_with_foreign_network():
    result_dtos = get_TVmaze_response_DTOs_from_json("foreign_network.json")

    model = SearchResults.from_tvmaze_dto_list(result_dtos)

    assert len(model.results) == 1
    result = model.results[0]
    assert result.network == "BBC One"
    assert result.network_country == "United Kingdom"


def test_result_with_network_with_no_country():
    # probably won't occur in real data
    result_dtos = get_TVmaze_response_DTOs_from_json("network_no_country.json")

    model = SearchResults.from_tvmaze_dto_list(result_dtos)

    assert len(model.results) == 1
    result = model.results[0]
    assert result.network == "BBC One"
    assert result.network_country is None


def test_result_with_streaming_service_with_country():
    result_dtos = get_TVmaze_response_DTOs_from_json("streaming_service.json")

    model = SearchResults.from_tvmaze_dto_list(result_dtos)

    assert len(model.results) == 1
    result = model.results[0]
    assert result.streaming_service == "BBC iPlayer"
    assert result.streaming_service_country == "United Kingdom"


def test_result_with_streaming_service_with_no_country():
    result_dtos = get_TVmaze_response_DTOs_from_json(
        "streaming_service_no_country.json"
    )

    model = SearchResults.from_tvmaze_dto_list(result_dtos)

    assert len(model.results) == 1
    result = model.results[0]
    assert result.streaming_service == "Netflix"
    assert result.streaming_service_country is None


def test_result_with_no_start_or_end_date():  # unlikely in real data
    result_dtos = get_TVmaze_response_DTOs_from_json("no_start_or_end_date.json")

    model = SearchResults.from_tvmaze_dto_list(result_dtos)

    assert len(model.results) == 1
    result = model.results[0]
    assert result.start_year is None
    assert result.end_year is None


def test_result_with_no_start_date():  # unlikely in real data
    result_dtos = get_TVmaze_response_DTOs_from_json("no_start_date.json")

    model = SearchResults.from_tvmaze_dto_list(result_dtos)

    assert len(model.results) == 1
    result = model.results[0]
    assert result.start_year is None
    assert result.end_year is not None


def test_result_with_no_end_date():
    result_dtos = get_TVmaze_response_DTOs_from_json("no_end_date.json")

    model = SearchResults.from_tvmaze_dto_list(result_dtos)

    assert len(model.results) == 1
    result = model.results[0]
    assert result.start_year is not None
    assert result.end_year is None
