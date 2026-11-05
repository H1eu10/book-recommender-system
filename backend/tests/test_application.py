from types import SimpleNamespace

import pytest

from app.book_service import load_books
from app import personalized_service as service


def test_legacy_preferences_route_still_works(client):
    payload = {"genres": ["fantasy"], "limit": 3}
    old = client.post("/api/recommendations", json=payload)
    current = client.post("/api/recommendations/smart", json=payload)
    assert old.status_code == current.status_code == 200
    assert old.json() == current.json()
    assert all(row["explanations"] for row in current.json())


def test_demo_profiles_and_model_options(client):
    profiles = client.get("/api/profiles")
    assert profiles.status_code == 200
    first = profiles.json()[0]
    detail = client.get(f"/api/profiles/{first['id']}")
    assert detail.status_code == 200
    assert detail.json()["synthetic"] is True
    assert len(detail.json()["liked_book_ids"]) == first["liked_count"]
    statuses = client.get("/api/models").json()
    assert {row["id"] for row in statuses} == set(service.MODEL_IDS)
    assert all(row["available"] for row in statuses if row["id"] in ("itemcf", "popularity"))
    assert client.get("/api/profiles/missing-user").status_code == 404


@pytest.mark.parametrize("model", ["popularity", "itemcf"])
def test_baseline_application_never_recommends_visible_likes(client, model):
    profile = client.get("/api/profiles/user_001").json()
    response = client.post("/api/recommendations/personalized",
                           json={"user_id": "user_001", "model": model, "limit": 5})
    assert response.status_code == 200
    body = response.json()
    assert body["score_type"] == "ranking"
    assert len(body["results"]) == 5
    assert not set(profile["liked_book_ids"]) & {row["book"]["id"] for row in body["results"]}


def test_neural_adapter_masks_full_history_and_preserves_raw_scores(client, monkeypatch, tmp_path):
    books = load_books()[:3]
    monkeypatch.setenv("BOOK_MODEL_DIR", str(tmp_path))
    (tmp_path / "lightgcn.pt").write_bytes(b"mock-checkpoint")
    monkeypatch.setattr(service, "load_profiles", lambda: {"demo": [books[0].id, books[1].id]})
    def recommend(user, limit, exclude):
        assert user == "demo"
        assert set(exclude) == {books[0].id, books[1].id}
        return [{"book_id": books[2].id, "score": -2.5}]
    model = SimpleNamespace(kind="lightgcn", recommend=recommend,
                            data=SimpleNamespace(train={"demo": [books[0].id]},
                                                 item_ids=[b.id for b in books]))
    monkeypatch.setattr(service, "_checkpoint", lambda *args: model)
    response = client.post("/api/recommendations/personalized", json={"user_id": "demo"})
    assert response.status_code == 200
    assert response.json()["results"][0]["score"] == -2.5


def test_missing_neural_checkpoint_returns_service_unavailable(client, monkeypatch, tmp_path):
    monkeypatch.setenv("BOOK_MODEL_DIR", str(tmp_path))
    response = client.post("/api/recommendations/personalized", json={"user_id": "user_001"})
    assert response.status_code == 503
    assert response.json() == {"detail": "Model unavailable"}


def test_corrupt_checkpoint_returns_service_unavailable(client, monkeypatch, tmp_path):
    monkeypatch.setenv("BOOK_MODEL_DIR", str(tmp_path))
    (tmp_path / "lightgcn.pt").write_bytes(b"not a valid model")
    response = client.post("/api/recommendations/personalized", json={"user_id": "user_001"})
    assert response.status_code == 503


@pytest.mark.parametrize("payload,status", [
    ({"user_id": "missing"}, 404),
    ({"user_id": " "}, 422),
    ({"user_id": "user_001", "model": "invalid"}, 422),
    ({"user_id": "user_001", "limit": 0}, 422),
    ({"user_id": "user_001", "limit": 21}, 422),
])
def test_personalized_validation(client, payload, status):
    assert client.post("/api/recommendations/personalized", json=payload).status_code == status
