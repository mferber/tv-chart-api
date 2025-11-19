import pytest

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
        web_host=None,
        web_host_country=None,
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
        web_host=None,
        web_host_country=None,
        summary_html="<p>Summary 2 truncated</p>",
        image_url="https://static.tvmaze.com/uploads/images/medium_portrait/6/17017.jpg",
    )


@pytest.mark.skip
def test_invalid_result_set_fails_validation():
    pass


@pytest.mark.skip
def test_result_with_all_optional_fields_missing():
    pass


@pytest.mark.skip
def test_result_with_us_network():
    pass


@pytest.mark.skip
def test_result_with_foreign_network():
    pass  # old Doctor Who


@pytest.mark.skip
def test_result_with_network_with_no_country():
    pass


@pytest.mark.skip
def test_result_with_streaming_service_with_country():
    pass  # Doctor Who BBC iPlayer


@pytest.mark.skip
def test_result_with_streaming_service_with_no_country():
    pass  # Bojack Horseman


@pytest.mark.skip
def test_result_with_no_start_or_end_date():
    pass


@pytest.mark.skip
def test_result_with_no_start_date():  # unlikely in real data
    pass


@pytest.mark.skip
def test_result_with_no_end_date():
    pass
