import pytest
from litestar.testing import TestClient


@pytest.mark.parametrize("login_as_user", ["test_user1"], indirect=True)
def test_user1_sees_own_shows(test_client: TestClient, login_as_user: None) -> None:
    rsp = test_client.get("/shows")
    rsp_contents = rsp.json()
    assert len(rsp_contents) == 1
    assert rsp_contents[0]["title"] == "All Creatures Great & Small"


@pytest.mark.parametrize("login_as_user", ["test_user2"], indirect=True)
def test_user2_sees_own_shows(
    test_client: TestClient, csrf_token_header: dict[str, str], login_as_user: None
) -> None:
    rsp = test_client.get("/shows")
    rsp_contents = rsp.json()
    assert len(rsp_contents) == 1
    assert rsp_contents[0]["title"] == "Pluribus"
