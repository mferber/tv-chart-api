from pathlib import Path

from pydantic import TypeAdapter

from tvmaze_api.models import TVmazeSearchResult


def read_sample(fname: str) -> str:
    return (Path(__file__).parent / fname).read_text()


def get_TVmaze_responses_from_json(fname: str) -> list[TVmazeSearchResult]:
    json = read_sample(fname)
    adapter = TypeAdapter(list[TVmazeSearchResult])
    return adapter.validate_json(json)
