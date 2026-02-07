from litestar import Litestar
from litestar.status_codes import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN
from litestar.testing import TestClient

"""Test authentication features. Note authentication is provided by litestar-users
and doesn't require much testing here.
"""


def test_unauthenticated_failure(test_client: TestClient[Litestar]) -> None:
    rsp = test_client.get("/shows")
    assert rsp.status_code == HTTP_401_UNAUTHORIZED


def test_csrf_failure(
    test_client: TestClient[Litestar], csrf_token_header: str
) -> None:
    """Test that POST is forbidden (403) with CSRF header omitted"""
    rsp = test_client.post(
        "/auth/login", json={"email": "invalid@nowhere.com", "password": "password"}
    )
    assert rsp.status_code == HTTP_403_FORBIDDEN
    assert "CSRF" in rsp.text


def test_invalid_login(
    test_client: TestClient[Litestar], csrf_token_header: dict[str, str]
) -> None:
    rsp = test_client.post(
        "/auth/login",
        json={"email": "invalid@nowhere.com", "password": "password"},
        headers=csrf_token_header,
    )
    assert rsp.status_code == HTTP_401_UNAUTHORIZED
