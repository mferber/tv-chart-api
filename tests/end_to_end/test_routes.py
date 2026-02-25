import pytest
import respx
from helpers.testing_data.mock_responses.reader import SampleFileReader
from helpers.testing_data.types import FakeUser
from litestar.testing import TestClient


@pytest.mark.parametrize("login_as_user", ["test_user1"], indirect=True)
def test_user1_sees_own_shows(test_client: TestClient, login_as_user: FakeUser) -> None:
    rsp = test_client.get("/shows")
    rsp.raise_for_status()
    rsp_contents = rsp.json()
    assert len(rsp_contents) == 1
    assert rsp_contents[0]["title"] == "All Creatures Great & Small"


@pytest.mark.parametrize("login_as_user", ["test_user2"], indirect=True)
def test_user2_sees_own_shows(test_client: TestClient, login_as_user: FakeUser) -> None:
    rsp = test_client.get("/shows")
    rsp.raise_for_status()
    rsp_contents = rsp.json()
    assert len(rsp_contents) == 1
    assert rsp_contents[0]["title"] == "Pluribus"


@pytest.mark.parametrize("login_as_user", ["test_user1"], indirect=True)
def test_get_show(test_client: TestClient, login_as_user: FakeUser) -> None:
    rsp = test_client.get("/shows")
    rsp.raise_for_status()
    first_show_json = rsp.json()[0]
    show_id = first_show_json["id"]

    show_rsp = test_client.get(f"/shows/{show_id}")
    show_rsp.raise_for_status()
    show_json = show_rsp.json()

    assert show_json["id"] == show_id
    assert show_json["title"] == first_show_json["title"]


@pytest.mark.parametrize("login_as_user", ["test_user1"], indirect=True)
@respx.mock(assert_all_mocked=True)
def test_add_show(
    test_client: TestClient, login_as_user: FakeUser, respx_mock: respx.MockRouter
) -> None:
    # this test uses TVmazeClient: mock out TVmaze URLs
    sample_file_reader = SampleFileReader("sample_tvmaze_show_responses")

    show_json = sample_file_reader.read("network_show.json")
    respx_mock.get("https://api.tvmaze.com/shows/6456").respond(text=show_json)

    episodes_json = sample_file_reader.read("network_show_episodes.json")
    respx_mock.get("https://api.tvmaze.com/shows/6456/episodes").respond(
        text=episodes_json
    )

    # precondition
    shows_before = test_client.get("/shows").json()
    assert len(shows_before) == 1

    # run test
    rsp = test_client.get("/add-show?tvmaze_id=6456")
    rsp.raise_for_status()

    shows_after = test_client.get("/shows").json()
    assert len(shows_after) == 2

    added = rsp.json()
    assert added["tvmaze_id"] == 6456
    assert added["title"] == "Counterpart"
    assert added["source"] == "STARZ"
    assert added["duration"] == 60
    assert added["imdb_id"] == "tt4643084"
    assert len(added["seasons"]) == 2
    assert len(added["seasons"][0]) == 10
    assert len(added["seasons"][1]) == 10
