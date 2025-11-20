import pytest

from pydantic import ValidationError

from tvmaze_api.search.models import SearchResult, SearchResults
from tvmaze_api.search.dtos import TVmazeSearchResultDTOs
from ..sample_results.reader import read_sample


def test_overall_result_set_validation():
    result_json = read_sample("multiple_results.json")
    resultsModel: SearchResults = TVmazeSearchResultDTOs.model_from_tvmaze_response(
        result_json
    )

    assert len(resultsModel.results) == 2
    assert resultsModel.results[0] == SearchResult(
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
    assert resultsModel.results[1] == SearchResult(
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
    with pytest.raises(ValidationError):
        result_json = read_sample("multiple_results_invalid.json")
        _: SearchResults = TVmazeSearchResultDTOs.model_from_tvmaze_response(
            result_json
        )


def test_result_with_all_optional_fields_missing():
    result_json = read_sample("optional_fields_missing.json")
    resultsModel: SearchResults = TVmazeSearchResultDTOs.model_from_tvmaze_response(
        result_json
    )
    result = resultsModel.results[0]

    assert result.genres is None
    assert result.start_year is None
    assert result.end_year is None
    assert result.network is None
    assert result.network_country is None
    assert result.streaming_service is None
    assert result.streaming_service_country is None
    assert result.summary_html is None
    assert result.image_url is None


def test_result_with_us_network():
    result_json = read_sample("us_network.json")
    resultsModel: SearchResults = TVmazeSearchResultDTOs.model_from_tvmaze_response(
        result_json
    )
    result = resultsModel.results[0]

    assert result.network == "Syfy"
    assert result.network_country == "United States"


def test_result_with_foreign_network():
    result_json = read_sample("foreign_network.json")
    resultsModel: SearchResults = TVmazeSearchResultDTOs.model_from_tvmaze_response(
        result_json
    )
    result = resultsModel.results[0]

    assert result.network == "BBC One"
    assert result.network_country == "United Kingdom"


def test_result_with_network_with_no_country():
    # probably won't occur in real data
    result_json = read_sample("network_no_country.json")
    resultsModel: SearchResults = TVmazeSearchResultDTOs.model_from_tvmaze_response(
        result_json
    )
    result = resultsModel.results[0]

    assert result.network == "BBC One"
    assert result.network_country is None


def test_result_with_streaming_service_with_country():
    result_json = read_sample("streaming_service.json")
    resultsModel: SearchResults = TVmazeSearchResultDTOs.model_from_tvmaze_response(
        result_json
    )
    result = resultsModel.results[0]

    assert result.streaming_service == "BBC iPlayer"
    assert result.streaming_service_country == "United Kingdom"


def test_result_with_streaming_service_with_no_country():
    result_json = read_sample("streaming_service_no_country.json")
    resultsModel: SearchResults = TVmazeSearchResultDTOs.model_from_tvmaze_response(
        result_json
    )
    result = resultsModel.results[0]

    assert result.streaming_service == "Netflix"
    assert result.streaming_service_country is None


def test_result_with_no_start_or_end_date():  # unlikely in real data
    result_json = read_sample("no_start_or_end_date.json")
    resultsModel: SearchResults = TVmazeSearchResultDTOs.model_from_tvmaze_response(
        result_json
    )
    result = resultsModel.results[0]

    assert result.start_year is None
    assert result.end_year is None


def test_result_with_no_start_date():  # unlikely in real data
    result_json = read_sample("no_start_date.json")
    resultsModel: SearchResults = TVmazeSearchResultDTOs.model_from_tvmaze_response(
        result_json
    )
    result = resultsModel.results[0]

    assert result.start_year is None
    assert result.end_year is not None


def test_result_with_no_end_date():
    result_json = read_sample("no_end_date.json")
    resultsModel: SearchResults = TVmazeSearchResultDTOs.model_from_tvmaze_response(
        result_json
    )
    result = resultsModel.results[0]

    assert result.start_year is not None
    assert result.end_year is None
