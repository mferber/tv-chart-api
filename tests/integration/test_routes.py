import pytest
from litestar.testing import TestClient

from integration.helpers.test_data.types import FakeUser


@pytest.mark.parametrize("login_as_user", ["test_user1"], indirect=True)
def test_user1_sees_own_shows(test_client: TestClient, login_as_user: FakeUser) -> None:
    rsp = test_client.get("/shows")
    rsp.raise_for_status()
    rsp_contents = rsp.json()
    assert len(rsp_contents) == 1
    assert rsp_contents[0]["title"] == "All Creatures Great & Small"


@pytest.mark.parametrize("login_as_user", ["test_user2"], indirect=True)
def test_user2_sees_own_shows(
    test_client: TestClient, csrf_token_header: dict[str, str], login_as_user: FakeUser
) -> None:
    rsp = test_client.get("/shows")
    rsp.raise_for_status()
    rsp_contents = rsp.json()
    assert len(rsp_contents) == 1
    assert rsp_contents[0]["title"] == "Pluribus"


@pytest.mark.parametrize("login_as_user", ["test_user1"], indirect=True)
def test_add_show(
    test_client: TestClient, login_as_user: FakeUser, csrf_token_header: dict[str, str]
) -> None:
    show = {
        "user_id": login_as_user.id,
        "tvmaze_id": 1001,
        "title": "Fictional Show",
        "source": "HBO",
        "duration": 60,
        "image_sm_url": "https://images.com/fictional/sm",
        "image_lg_url": "https://images.com/fictional/lg",
        "seasons": [],
    }
    rsp = test_client.post("/shows", json=show, headers=csrf_token_header)
    rsp.raise_for_status()
    added_id = rsp.json()["id"]
    rsp2 = test_client.get("/shows")
    rsp2_contents = rsp2.json()

    assert len(rsp2_contents) == 2
    added_show_json = next(filter(lambda obj: obj["id"] == added_id, rsp2_contents))
    assert added_show_json is not None
    assert added_show_json.get("user_id") is None
    assert added_show_json["tvmaze_id"] == 1001
    assert added_show_json["title"] == "Fictional Show"
    assert added_show_json["source"] == "HBO"
    assert added_show_json["duration"] == 60
    assert added_show_json["image_sm_url"] == "https://images.com/fictional/sm"
    assert added_show_json["image_lg_url"] == "https://images.com/fictional/lg"
    assert added_show_json["seasons"] == []
