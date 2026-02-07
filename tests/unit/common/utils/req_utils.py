from litestar.testing import TestClient

from app import CSRF_HEADER_NAME


def make_csrf_token_header(csrf_token: str) -> dict[str, str]:
    """Generates the CSRF header for inclusion in unsafe requests, given the token"""

    return {CSRF_HEADER_NAME: csrf_token}


def login(
    test_client: TestClient,
    csrf_token_header: dict[str, str],
    email: str,
    password: str,
) -> None:
    # automatically sets JWT cookie on TestClient
    rsp = test_client.post(
        "/auth/login",
        json={"email": email, "password": password},
        headers=csrf_token_header,
    )
    rsp.raise_for_status()
