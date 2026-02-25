from pathlib import Path

from tvmaze_api.models import TVmazeSearchResultList


def read_sample(fname: str) -> str:
    return (Path(__file__).parent / fname).read_text()


def get_TVmaze_responses_from_json(fname: str) -> TVmazeSearchResultList:
    json = read_sample(fname)
    return TVmazeSearchResultList.model_validate_json(json)
