from litestar import Litestar
from litestar.status_codes import HTTP_200_OK
from litestar.testing import TestClient

"""Test routes that don't require authentication."""


def test_health_check(test_client: TestClient[Litestar]) -> None:
    rsp = test_client.get("/health")
    assert rsp.status_code == HTTP_200_OK
    assert rsp.text == "OK"


def test_app_env(test_client: TestClient[Litestar]) -> None:
    rsp = test_client.get("/env")
    assert rsp.status_code == HTTP_200_OK

    # value is set in the environment variables set up for the
    # test_app fixture
    assert rsp.text == "testing"
