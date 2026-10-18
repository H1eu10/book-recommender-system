import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"genres": [], "tags": []},
        {"genres": ["   "]},
        {"genres": ["fantasy"], "max_pages": 0},
        {"genres": ["fantasy"], "limit": 0},
        {"genres": ["fantasy"], "limit": 21},
    ],
)
def test_invalid_recommendation_requests(client, payload):
    response = client.post(
        "/api/recommendations",
        json=payload,
    )

    assert response.status_code == 422
    assert "detail" in response.json()