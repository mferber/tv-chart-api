from litestar import Litestar
from litestar.status_codes import HTTP_200_OK
from litestar.testing import TestClient


def test_health_check(test_app: Litestar) -> None:
    with TestClient(app=test_app) as client:
        response = client.get("/health")
        assert response.status_code == HTTP_200_OK
        assert response.text == "OK"


def test_app_env(test_app: Litestar) -> None:
    with TestClient(app=test_app) as client:
        response = client.get("/env")
        assert response.status_code == HTTP_200_OK

        # value is set in the environment variables set up for the
        # test_app fixture
        assert response.text == "testing"
