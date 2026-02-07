from litestar.testing import TestClient
from unit.common.utils.req_utils import login


def test_user1_shows(
    test_client: TestClient, csrf_token_header: dict[str, str]
) -> None:
    login(
        email="testuser1@example.com",
        password="password1",
        test_client=test_client,
        csrf_token_header=csrf_token_header,
    )
    rsp = test_client.get("/shows")
    rsp_contents = rsp.json()
    assert len(rsp_contents) == 1
    assert rsp_contents[0]["title"] == "All Creatures Great & Small"


def test_user2_shows(
    test_client: TestClient, csrf_token_header: dict[str, str]
) -> None:
    login(
        email="testuser2@example.com",
        password="password2",
        test_client=test_client,
        csrf_token_header=csrf_token_header,
    )
    rsp = test_client.get("/shows")
    rsp_contents = rsp.json()
    assert len(rsp_contents) == 1
    assert rsp_contents[0]["title"] == "Pluribus"
