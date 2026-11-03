import pytest
from fastapi.testclient import TestClient

from app.content_based import ContentBasedIndex, get_index
from app.main import app
from app.schemas import Book


@pytest.fixture
def books():
    return [
        Book(
            id="b1", title="Fantasy Adventure", author="Author A",
            genres=["fantasy", "adventure"], tags=["magic", "quest"],
            description="A magical quest.", language="en", pages=300,
        ),
        Book(
            id="b2", title="Fantasy Quest", author="Author B",
            genres=["fantasy"], tags=["magic", "dragon"],
            description="A dragon quest.", language="en", pages=250,
        ),
        Book(
            id="b3", title="Science Manual", author="Author C",
            genres=["science-fiction"], tags=["space", "aliens"],
            description="A space adventure.", language="en", pages=400,
        ),
        Book(
            id="b4", title="Romance Novel", author="Author D",
            genres=["romance"], tags=["love", "family"],
            description="A love story.", language="vi", pages=200,
        ),
    ]


@pytest.fixture
def index(books):
    return ContentBasedIndex(books)


# -- similar ----------------------------------------------------------

def test_similar_returns_related_books(index):
    results = index.similar("b1", limit=2)
    assert len(results) >= 1
    assert results[0].book.id == "b2"  # shares fantasy + magic
    assert all(r.book.id != "b1" for r in results)


def test_similar_unknown_book(index):
    assert index.similar("nonexistent") == []


def test_similar_respects_limit(index):
    results = index.similar("b1", limit=1)
    assert len(results) <= 1


def test_similar_returns_reasons(index):
    results = index.similar("b1", limit=1)
    assert len(results) == 1
    reasons = " ".join(results[0].reasons)
    assert "fantasy" in reasons.lower() or "magic" in reasons.lower()


# -- by_preferences ---------------------------------------------------

def test_by_preferences_filters_language(index):
    results = index.by_preferences(
        genres=["fantasy"], tags=["magic"], language="vi",
    )
    assert results == []


def test_by_preferences_filters_max_pages(index):
    results = index.by_preferences(genres=["fantasy"], max_pages=100)
    assert results == []


def test_by_preferences_returns_matches(index):
    results = index.by_preferences(
        genres=["fantasy"], tags=["magic"], limit=5,
    )
    assert len(results) >= 1
    assert results[0].book.id in {"b1", "b2"}


def test_by_preferences_empty_query(index):
    assert index.by_preferences(genres=[], tags=[]) == []


def test_by_preferences_sorted_descending(index):
    results = index.by_preferences(
        genres=["fantasy"], tags=["magic"], limit=5,
    )
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)


# -- cache ------------------------------------------------------------

def test_get_index_caches_by_id(books):
    idx1 = get_index(books)
    idx2 = get_index(books)
    assert idx1 is idx2


# -- API integration --------------------------------------------------

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_api_similar_returns_404_for_unknown(client):
    response = client.post(
        "/api/recommendations/similar",
        json={"book_id": "definitely-not-a-real-id", "limit": 5},
    )
    assert response.status_code == 404


def test_api_similar_returns_results(client):
    books_resp = client.get("/api/books")
    assert books_resp.status_code == 200
    books = books_resp.json()
    if not books:
        pytest.skip("No books loaded — run crawl first")

    book_id = books[0]["id"]
    response = client.post(
        "/api/recommendations/similar",
        json={"book_id": book_id, "limit": 3},
    )
    assert response.status_code == 200
    results = response.json()
    assert isinstance(results, list)
    assert len(results) <= 3
    for r in results:
        assert r["book"]["id"] != book_id
        assert 0 < r["score"] <= 1


def test_api_smart_returns_results(client):
    response = client.post(
        "/api/recommendations/smart",
        json={"genres": ["fantasy"], "limit": 5},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_api_smart_rejects_empty_query(client):
    response = client.post(
        "/api/recommendations/smart",
        json={"genres": [], "tags": []},
    )
    assert response.status_code == 422