import pytest
import respx
from helpers.testing_data.import_data.reader import (
    SampleFileReader as SampleImportFileReader,
)
from helpers.testing_data.mock_responses.reader import (
    SampleFileReader as SampleResponseFileReader,
)
from helpers.testing_data.types import FakeUser
from litestar.status_codes import HTTP_400_BAD_REQUEST
from litestar.testing import TestClient

from services.import_service import ImportService


@pytest.mark.parametrize("login_as_user", ["test_user1"], indirect=True)
def test_user1_sees_own_shows(test_client: TestClient, login_as_user: FakeUser) -> None:
    rsp = test_client.get("/shows")
    rsp.raise_for_status()
    rsp_contents = rsp.json()
    assert len(rsp_contents) == 1
    assert next(iter(rsp_contents.values()))["title"] == "All Creatures Great & Small"


@pytest.mark.parametrize("login_as_user", ["test_user2"], indirect=True)
def test_user2_sees_own_shows(test_client: TestClient, login_as_user: FakeUser) -> None:
    rsp = test_client.get("/shows")
    rsp.raise_for_status()
    rsp_contents = rsp.json()
    assert len(rsp_contents) == 2
    titles = [show["title"] for show in rsp_contents.values()]
    assert "Pluribus" in titles
    assert "Severance" in titles


@pytest.mark.parametrize("login_as_user", ["test_user1"], indirect=True)
def test_get_show(test_client: TestClient, login_as_user: FakeUser) -> None:
    rsp = test_client.get("/shows")
    rsp.raise_for_status()
    first_show_json = next(iter(rsp.json().values()))
    show_id = first_show_json["id"]

    show_rsp = test_client.get(f"/shows/{show_id}")
    show_rsp.raise_for_status()
    show_json = show_rsp.json()

    assert show_json["id"] == show_id
    assert show_json["title"] == first_show_json["title"]


@pytest.mark.parametrize("login_as_user", ["test_user1"], indirect=True)
@respx.mock(assert_all_mocked=True)
def test_add_show_adds_show_to_db(
    test_client: TestClient, login_as_user: FakeUser, respx_mock: respx.MockRouter
) -> None:
    # this test uses TVmazeClient: mock out TVmaze URLs
    sample_file_reader = SampleResponseFileReader("sample_tvmaze_show_responses")

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


@pytest.mark.parametrize("login_as_user", ["test_user1"], indirect=True)
@respx.mock(assert_all_mocked=True)
def test_get_episodes(
    test_client: TestClient, login_as_user: FakeUser, respx_mock: respx.MockRouter
) -> None:
    # this test uses TVmazeClient: mock out TVmaze URLs
    sample_file_reader = SampleResponseFileReader("sample_tvmaze_show_responses")
    fake_episodes_json = sample_file_reader.read("network_show_episodes.json")
    respx_mock.get("https://api.tvmaze.com/shows/42836/episodes").respond(
        text=fake_episodes_json
    )

    shows_json = test_client.get("/shows").json()
    all_creatures = next(
        filter(lambda show: show["tvmaze_id"] == 42836, shows_json.values())
    )

    rsp = test_client.get(f"/episodes/{all_creatures['id']}")
    rsp.raise_for_status()

    episodes_json: list[list[dict]] = rsp.json()
    assert len(episodes_json) == 2
    assert len(episodes_json[0]) == 10
    assert len(episodes_json[1]) == 10
    assert episodes_json[0][0]["title"] == "The Crossing"
    assert (
        episodes_json[0][0]["summary"]
        and "Howard Silk" in episodes_json[0][0]["summary"]
    )
    assert episodes_json[0][0]["type"] == "episode"
    assert episodes_json[0][0]["duration"] == 60
    assert episodes_json[0][0]["release_date"] == "2017-12-10"


@pytest.mark.parametrize("login_as_user", ["test_user1"], indirect=True)
@respx.mock(assert_all_mocked=True)
def test_get_episodes_with_force_refresh(
    test_client: TestClient, login_as_user: FakeUser, respx_mock: respx.MockRouter
) -> None:
    # this test uses TVmazeClient: mock out TVmaze URLs
    sample_file_reader = SampleResponseFileReader("sample_tvmaze_show_responses")
    fake_episodes_json = sample_file_reader.read("network_show_episodes.json")
    route = respx_mock.get("https://api.tvmaze.com/shows/42836/episodes").respond(
        text=fake_episodes_json
    )

    shows_json = test_client.get("/shows").json()
    all_creatures = next(
        filter(lambda show: show["tvmaze_id"] == 42836, shows_json.values())
    )

    # run test
    _ = test_client.get(f"/episodes/{all_creatures['id']}")  # caches result
    rsp = test_client.get(
        f"/episodes/{all_creatures['id']}", params={"forcerefresh": "true"}
    )  # caches result
    rsp.raise_for_status()

    assert route.call_count == 2  # skipped cache on second call

    episodes_json = rsp.json()
    assert episodes_json[0][0]["title"] == "The Crossing"
    assert (
        episodes_json[0][0]["summary"]
        and "Howard Silk" in episodes_json[0][0]["summary"]
    )
    assert episodes_json[0][0]["type"] == "episode"
    assert episodes_json[0][0]["duration"] == 60
    assert episodes_json[0][0]["release_date"] == "2017-12-10"


@pytest.mark.parametrize("login_as_user", ["test_user1"], indirect=True)
def test_toggle_watched_status(
    test_client: TestClient, login_as_user: FakeUser, csrf_token_header: dict[str, str]
) -> None:
    shows_json = test_client.get("/shows").json()
    all_creatures_json = next(
        filter(lambda show: show["tvmaze_id"] == 42836, shows_json.values())
    )
    all_creatures_id = all_creatures_json["id"]

    # precondition (first season is marked watched)
    assert all_creatures_json["seasons"][0][0]["watched"]
    assert not (all_creatures_json["seasons"][1][0]["watched"])

    test_client.post(
        "/toggle-watched-status",
        json={
            "show_id": all_creatures_id,
            "episodes": [[0, 0], [1, 0]],
        },
        headers=csrf_token_header,
    )

    updated_json = test_client.get(f"/shows/{all_creatures_id}").json()

    assert not (updated_json["seasons"][0][0]["watched"])
    assert updated_json["seasons"][1][0]["watched"]


@pytest.mark.parametrize("login_as_user", ["test_user2"], indirect=True)
def test_delete_show(
    test_client: TestClient, login_as_user: FakeUser, csrf_token_header: dict[str, str]
) -> None:
    shows_before = test_client.get("/shows").json()
    show_to_delete = next(iter(shows_before.values()))

    deleted_show = test_client.delete(
        f"/shows/{show_to_delete['id']}", headers=csrf_token_header
    ).json()

    shows_after = test_client.get("/shows").json()
    assert len(shows_after) == len(shows_before) - 1
    assert deleted_show == show_to_delete


@pytest.mark.parametrize("login_as_user", ["test_user2"], indirect=True)
def test_toggle_favorite(
    test_client: TestClient, login_as_user: FakeUser, csrf_token_header: dict[str, str]
) -> None:
    shows_before = test_client.get("/shows").json()
    show_to_toggle = next(iter(shows_before.values()))
    orig_favorite = show_to_toggle["favorite"]

    returned_show = test_client.post(
        "/toggle-favorite",
        headers=csrf_token_header,
        json={"show_id": show_to_toggle["id"]},
    )

    returned_show.raise_for_status()
    show_after = test_client.get(f"/shows/{show_to_toggle['id']}").json()
    assert show_after["favorite"] != orig_favorite


@pytest.mark.parametrize("login_as_user", ["test_user2"], indirect=True)
def test_update_user_fields(
    test_client: TestClient, login_as_user: FakeUser, csrf_token_header: dict[str, str]
) -> None:
    shows_before = test_client.get("/shows").json()
    print(shows_before)
    show_to_edit = next(
        iter(filter(lambda show: show["title"] == "Pluribus", shows_before.values()))
    )

    returned_show = test_client.post(
        "/update-user-fields",
        headers=csrf_token_header,
        json={
            "show_id": show_to_edit["id"],
            "user_channel": "new channel",
            "user_notes": "new notes",
        },
    )

    returned_show.raise_for_status()
    show_after = test_client.get(f"/shows/{show_to_edit['id']}").json()
    assert show_after["user_channel"] == "new channel"
    assert show_after["user_notes"] == "new notes"


@pytest.mark.parametrize("login_as_user", ["test_user2"], indirect=True)
def test_export_show_data(test_client: TestClient, login_as_user: FakeUser) -> None:
    exported_data = test_client.get("/data/export").text

    # validate as if we were importing
    ImportService.schema_validate_import_data(exported_data)
    # see integration tests for checks on full details of exported data


@pytest.mark.parametrize("login_as_user", ["test_user1"], indirect=True)
def test_import_show_data(
    test_client: TestClient, login_as_user: FakeUser, csrf_token_header: dict[str, str]
) -> None:
    shows_before = test_client.get("/shows").json()
    assert len(shows_before) != 2  # precondition

    import_file = SampleImportFileReader().read("import_v0.0.1.json")
    rsp = test_client.post(
        "/data/import",
        files={"file": import_file.encode("utf-8")},
        headers=csrf_token_header,
    )
    rsp.raise_for_status()

    shows_after = test_client.get("/shows").json()
    assert len(shows_after) == 2
    imported_titles = [show["title"] for show in shows_after.values()]
    assert "Sherlock" in imported_titles
    assert "Battlestar Galactica" in imported_titles
    # see integration tests for checks on full details of imported data


@pytest.mark.parametrize("login_as_user", ["test_user1"], indirect=True)
def test_import_show_data_invalid_UTF_8(
    test_client: TestClient, login_as_user: FakeUser, csrf_token_header: dict[str, str]
) -> None:
    rsp = test_client.post(
        "/data/import",
        files={"file": b"\xff\xfe"},
        headers=csrf_token_header,
    )

    assert rsp.status_code == HTTP_400_BAD_REQUEST
    rsp_json = rsp.json()
    assert rsp_json["error"] == "invalid UTF-8 content"
    assert rsp_json["message"] != ""
    assert rsp_json["source"] != ""


@pytest.mark.parametrize("login_as_user", ["test_user1"], indirect=True)
def test_import_show_data_malformed_JSON(
    test_client: TestClient, login_as_user: FakeUser, csrf_token_header: dict[str, str]
) -> None:
    rsp = test_client.post(
        "/data/import",
        files={"file": b'{malformed: "data"}'},
        headers=csrf_token_header,
    )

    assert rsp.status_code == HTTP_400_BAD_REQUEST
    rsp_json = rsp.json()
    assert rsp_json["error"] == "invalid or malformed JSON"
    assert rsp_json["message"] != ""
    assert rsp_json["source"] != ""


@pytest.mark.parametrize("login_as_user", ["test_user1"], indirect=True)
def test_import_show_data_invalid_JSON(
    test_client: TestClient, login_as_user: FakeUser, csrf_token_header: dict[str, str]
) -> None:
    import_file = SampleImportFileReader().read("import_schema_invalid_v0.0.1.json")

    rsp = test_client.post(
        "/data/import",
        files={"file": import_file.encode("utf-8")},
        headers=csrf_token_header,
    )

    assert rsp.status_code == HTTP_400_BAD_REQUEST
    rsp_json = rsp.json()
    assert rsp_json["error"] == "invalid or malformed JSON"
    assert rsp_json["message"] != ""
    assert rsp_json["source"] != ""
