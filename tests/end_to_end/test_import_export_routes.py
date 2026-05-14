import pytest
from helpers.sample_file_reader import SampleFileReader
from helpers.testing_data.types import FakeUser
from litestar.status_codes import HTTP_400_BAD_REQUEST
from litestar.testing import TestClient

from services.import_service import ImportService

"""Source directory for test files read by SampleFileReader"""
TEST_DATA_DIR = "import_data_files"


@pytest.mark.parametrize("login_as_user", ["test_user2"], indirect=True)
def test_export_show_data(test_client: TestClient, login_as_user: FakeUser) -> None:
    exported_data = test_client.get("/data/export").text

    # validate as if we were importing
    ImportService.validate_import_data(exported_data)
    # see integration tests for checks on full details of exported data


@pytest.mark.parametrize("login_as_user", ["test_user1"], indirect=True)
def test_import_show_data(
    test_client: TestClient, login_as_user: FakeUser, reader: SampleFileReader, csrf_token_header: dict[str, str]
) -> None:
    shows_before = test_client.get("/shows").json()
    assert len(shows_before) != 2  # precondition

    import_file = reader.read("import_v0.0.1.json")
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
    assert rsp_json["details"] != ""


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
    assert rsp_json["details"] != ""


@pytest.mark.parametrize("login_as_user", ["test_user1"], indirect=True)
def test_import_show_data_invalid_JSON(
    test_client: TestClient, login_as_user: FakeUser, reader: SampleFileReader, csrf_token_header: dict[str, str]
) -> None:
    import_file = reader.read("import_schema_invalid_v0.0.1.json")

    rsp = test_client.post(
        "/data/import",
        files={"file": import_file.encode("utf-8")},
        headers=csrf_token_header,
    )

    assert rsp.status_code == HTTP_400_BAD_REQUEST
    rsp_json = rsp.json()
    assert rsp_json["error"] == "invalid or malformed JSON"
    assert rsp_json["message"] != ""
    assert rsp_json["details"] != ""