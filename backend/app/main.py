from fastapi import FastAPI, HTTPException

from app.book_service import load_books
from app.content_based import get_index
from app.recommendation_service import recommend_books
from app.schemas import (
    Book,
    RecommendationRequest,
    RecommendationResult,
    SimilarRequest,
)


app = FastAPI(title="Book Recommendation API")


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/books", response_model=list[Book])
def get_books():
    return load_books()


@app.post(
    "/api/recommendations",
    response_model=list[RecommendationResult],
)
def get_recommendations(preferences: RecommendationRequest):
    """Original rule-based recommendations (kept for comparison)."""
    books = load_books()
    return recommend_books(books, preferences)


@app.post(
    "/api/recommendations/similar",
    response_model=list[RecommendationResult],
)
def get_similar_books(request: SimilarRequest):
    """Item-to-item: find books similar to a given book."""
    books = load_books()
    if request.book_id not in {b.id for b in books}:
        raise HTTPException(status_code=404, detail="Book not found")
    index = get_index(books)
    return index.similar(request.book_id, request.limit)


@app.post(
    "/api/recommendations/smart",
    response_model=list[RecommendationResult],
)
def get_smart_recommendations(preferences: RecommendationRequest):
    """TF-IDF based recommendations from user preferences."""
    books = load_books()
    index = get_index(books)
    return index.by_preferences(
        genres=preferences.genres,
        tags=preferences.tags,
        language=preferences.language,
        max_pages=preferences.max_pages,
        limit=preferences.limit,
    )