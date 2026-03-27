import httpx
from litestar.testing import TestClient

from create_app import RATE_LIMIT_REQ_PER_MIN


def test_rate_limiting(test_client: TestClient) -> None:
    for i in range(0, RATE_LIMIT_REQ_PER_MIN):
        resp = test_client.get("/health")
        assert resp.status_code == httpx.codes.OK

    fail_resp = test_client.get("/health")
    assert fail_resp.status_code == httpx.codes.TOO_MANY_REQUESTS
