from fastapi import FastAPI

from app.book_service import load_books
from app.recommendation_service import recommend_books
from app.schemas import (
    Book,
    RecommendationRequest,
    RecommendationResult,
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
    books = load_books()
    return recommend_books(books, preferences)