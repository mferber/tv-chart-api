"""Tests for SearchResult and SearchResults models.

Verifies that TVmaze result sets are transformed to domain SearchResults models as
expected.
"""

import pytest
from pydantic import HttpUrl, ValidationError

from models.search import SearchResult
from tvmaze_api.models import TVmazeSearchResult

from ..sample_tvmaze_responses.reader import get_TVmaze_responses_from_json


def test_valid_result_set() -> None:
    results = get_TVmaze_responses_from_json("multiple_results.json")

    model = TVmazeSearchResult.to_search_results_model(results)

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
        image_sm_url=HttpUrl(
            "https://static.tvmaze.com/uploads/images/medium_portrait/0/2313.jpg"
        ),
        image_lg_url=HttpUrl(
            "https://static.tvmaze.com/uploads/images/original_untouched/0/2313.jpg"
        ),
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
        image_sm_url=HttpUrl(
            "https://static.tvmaze.com/uploads/images/medium_portrait/6/17017.jpg"
        ),
        image_lg_url=HttpUrl(
            "https://static.tvmaze.com/uploads/images/original_untouched/6/17017.jpg"
        ),
    )


def test_invalid_result_set_fails_validation() -> None:
    with pytest.raises(ValidationError):
        results = get_TVmaze_responses_from_json("multiple_results_invalid.json")
        _ = TVmazeSearchResult.to_search_results_model(results)


def test_result_with_all_optional_fields_missing() -> None:
    results = get_TVmaze_responses_from_json("optional_fields_missing.json")

    model = TVmazeSearchResult.to_search_results_model(results)

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
    assert result.image_sm_url is None
    assert result.image_lg_url is None


def test_result_with_US_network() -> None:
    results = get_TVmaze_responses_from_json("us_network.json")

    model = TVmazeSearchResult.to_search_results_model(results)

    assert len(model.results) == 1
    result = model.results[0]
    assert result.network == "Syfy"
    assert result.network_country == "United States"


def test_result_with_foreign_network() -> None:
    results = get_TVmaze_responses_from_json("foreign_network.json")

    model = TVmazeSearchResult.to_search_results_model(results)

    assert len(model.results) == 1
    result = model.results[0]
    assert result.network == "BBC One"
    assert result.network_country == "United Kingdom"


def test_result_with_network_with_no_country() -> None:
    # probably won't occur in real data
    results = get_TVmaze_responses_from_json("network_no_country.json")

    model = TVmazeSearchResult.to_search_results_model(results)

    assert len(model.results) == 1
    result = model.results[0]
    assert result.network == "BBC One"
    assert result.network_country is None


def test_result_with_streaming_service_with_country() -> None:
    results = get_TVmaze_responses_from_json("streaming_service.json")

    model = TVmazeSearchResult.to_search_results_model(results)

    assert len(model.results) == 1
    result = model.results[0]
    assert result.streaming_service == "BBC iPlayer"
    assert result.streaming_service_country == "United Kingdom"


def test_result_with_streaming_service_with_no_country() -> None:
    results = get_TVmaze_responses_from_json("streaming_service_no_country.json")

    model = TVmazeSearchResult.to_search_results_model(results)

    assert len(model.results) == 1
    result = model.results[0]
    assert result.streaming_service == "Netflix"
    assert result.streaming_service_country is None


def test_result_with_no_start_or_end_date() -> None:  # unlikely in real data
    results = get_TVmaze_responses_from_json("no_start_or_end_date.json")

    model = TVmazeSearchResult.to_search_results_model(results)

    assert len(model.results) == 1
    result = model.results[0]
    assert result.start_year is None
    assert result.end_year is None


def test_result_with_no_start_date() -> None:  # unlikely in real data
    results = get_TVmaze_responses_from_json("no_start_date.json")

    model = TVmazeSearchResult.to_search_results_model(results)

    assert len(model.results) == 1
    result = model.results[0]
    assert result.start_year is None
    assert result.end_year is not None


def test_result_with_no_end_date() -> None:
    results = get_TVmaze_responses_from_json("no_end_date.json")

    model = TVmazeSearchResult.to_search_results_model(results)

    assert len(model.results) == 1
    result = model.results[0]
    assert result.start_year is not None
    assert result.end_year is None


def test_summary_html_is_sanitized() -> None:
    results = get_TVmaze_responses_from_json("unsafe_html_summary.json")

    model = TVmazeSearchResult.to_search_results_model(results)

    assert len(model.results) == 1
    result = model.results[0]
    assert (
        result.summary_html == """<p>Paragraph 1</p>"""
        """<p>Paragraph 2 link text</p>"""
        """<p>Paragraph 3 <strong><em>bold + italic</em></strong> plain <strong>bold css</strong> <em>italic css</em> margin css</p>"""
        """<p>Paragraph 4 </p>"""
        """<p>Paragraph 5 </p>"""
        """<p>Paragraph 6 bare ampersand &amp; more text</p>"""
    )
