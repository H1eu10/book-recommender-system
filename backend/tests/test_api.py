import pytest


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
        "/api/recommendations/smart",
        json=payload,
    )

    assert response.status_code == 422
    assert "detail" in response.json()
