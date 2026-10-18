import pytest

from app.recommendation_service import recommend_books
from app.schemas import Book, RecommendationRequest


@pytest.fixture
def books():
    return [
        Book(
            id="test-001",
            title="Test Fantasy",
            author="Test Author",
            genres=["fantasy", "mystery"],
            tags=["magic"],
            description="Test description.",
            language="en",
            pages=240,
        ),
        Book(
            id="test-002",
            title="Test Family",
            author="Test Author",
            genres=["contemporary"],
            tags=["family"],
            description="Test description.",
            language="en",
            pages=190,
        ),
        Book(
            id="test-003",
            title="Test Space",
            author="Test Author",
            genres=["science-fiction"],
            tags=["space"],
            description="Test description.",
            language="en",
            pages=320,
        ),
    ]


def test_weighted_scores_and_order(books):
    preferences = RecommendationRequest(
        genres=["fantasy", "mystery"],
        tags=["magic", "family"],
    )

    results = recommend_books(books, preferences)

    assert [result.book.id for result in results] == [
        "test-001",
        "test-002",
    ]
    assert results[0].score == pytest.approx(0.85)
    assert results[1].score == pytest.approx(0.15)
    assert results[0].reasons == [
        "Matches your preferred genres: fantasy, mystery.",
        "Matches your preferred topics: magic.",
    ]


def test_genre_only_can_have_full_score(books):
    preferences = RecommendationRequest(
        genres=["science-fiction"],
    )

    results = recommend_books(books, preferences)

    assert len(results) == 1
    assert results[0].book.id == "test-003"
    assert results[0].score == pytest.approx(1.0)


def test_max_pages_excludes_long_books(books):
    preferences = RecommendationRequest(
        genres=["science-fiction"],
        max_pages=100,
    )

    assert recommend_books(books, preferences) == []


def test_language_is_a_mandatory_filter(books):
    preferences = RecommendationRequest(
        genres=["fantasy"],
        language="ru",
    )

    assert recommend_books(books, preferences) == []


def test_unknown_page_count_is_excluded_with_page_limit(books):
    book = books[0].model_copy(update={"pages": None})

    preferences = RecommendationRequest(
        genres=["fantasy"],
        max_pages=300,
    )

    assert recommend_books([book], preferences) == []


def test_result_limit(books):
    preferences = RecommendationRequest(
        genres=["fantasy"],
        tags=["family"],
        limit=1,
    )

    results = recommend_books(books, preferences)

    assert len(results) == 1
    assert results[0].book.id == "test-001"


def test_preferences_are_normalized():
    preferences = RecommendationRequest(
        genres=[" Fantasy ", "fantasy", ""],
        tags=[" MAGIC ", "magic"],
    )

    assert preferences.genres == ["fantasy"]
    assert preferences.tags == ["magic"]


def test_equal_scores_are_sorted_by_id(books):
    first = books[0].model_copy(update={"id": "a"})
    second = books[0].model_copy(update={"id": "b"})

    preferences = RecommendationRequest(genres=["fantasy"])

    results = recommend_books([second, first], preferences)

    assert [result.book.id for result in results] == ["a", "b"]