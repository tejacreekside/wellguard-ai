from fastapi.testclient import TestClient

from app.main import app


def test_direct_backend_serves_api_prefixed_routes():
    response = TestClient(app).get("/api/portfolio/summary")

    assert response.status_code == 200
    assert response.json()["well_count"] > 0
