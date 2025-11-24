from pathlib import Path

from pydantic import TypeAdapter

from tvmaze_api.dtos.search_dtos import TVmazeSearchResultDTO


def read_sample(fname: str) -> str:
    return (Path(__file__).parent / fname).read_text()


def get_TVmaze_response_DTOs_from_json(fname: str) -> list[TVmazeSearchResultDTO]:
    json = (Path(__file__).parent / fname).read_text()
    adapter = TypeAdapter(list[TVmazeSearchResultDTO])
    return adapter.validate_json(json)
