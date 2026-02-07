from litestar import Litestar
from litestar.status_codes import HTTP_401_UNAUTHORIZED
from litestar.testing import TestClient

"""Test authentication features. Note authentication is provided by litestar-users
and doesn't require much testing here.
"""


def test_unauthenticated_failure(test_client: TestClient[Litestar]) -> None:
    rsp = test_client.get("/shows")
    assert rsp.status_code == HTTP_401_UNAUTHORIZED
