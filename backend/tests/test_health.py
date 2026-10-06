from fastapi.testclient import TestClient


def test_health_reports_ok(client: TestClient) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_is_mounted_under_api_prefix(client: TestClient) -> None:
    """The frontend calls /api/*; a bare /health would mean a broken contract."""
    assert client.get("/health").status_code == 404
