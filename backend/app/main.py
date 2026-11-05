from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

from app.book_service import load_books
from app.content_based import get_index
from app.schemas import (
    Book,
    RecommendationRequest,
    RecommendationResult,
    SimilarRequest,
    PersonalizedRequest,
    PersonalizedResponse,
    RecommendationExplanation,
)
from app.personalized_service import available_models, load_profiles, personalized_recommendations
from app.book_service import PROJECT_ROOT


app = FastAPI(title="Book Recommendation API")


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/books", response_model=list[Book])
def get_books():
    return load_books()


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
    results = index.similar(request.book_id, request.limit)
    query = next(book for book in books if book.id == request.book_id)
    return explain_content(results, query.genres, query.tags, similar=True)


@app.post("/api/recommendations", response_model=list[RecommendationResult], include_in_schema=False)
@app.post(
    "/api/recommendations/smart",
    response_model=list[RecommendationResult],
)
def get_smart_recommendations(preferences: RecommendationRequest):
    """TF-IDF based recommendations from user preferences."""
    books = load_books()
    index = get_index(books)
    results = index.by_preferences(
        genres=preferences.genres,
        tags=preferences.tags,
        language=preferences.language,
        max_pages=preferences.max_pages,
        limit=preferences.limit,
    )
    return explain_content(results, preferences.genres, preferences.tags)


def explain_content(results, genres, tags, similar=False):
    for result in results:
        explanations = []
        for code, wanted, actual in (("genres", genres, result.book.genres),
                                      ("themes", tags, result.book.tags)):
            matched = sorted(set(wanted) & set(actual))
            if matched:
                explanations.append(RecommendationExplanation(
                    code=f"shared_{code}" if similar else code, values=matched))
        result.explanations = explanations or [RecommendationExplanation(code="text_similarity")]
    return results


@app.get("/api/models")
def get_models():
    return available_models()


@app.get("/api/profiles")
def get_profiles():
    return [{"id": user, "liked_count": len(liked)} for user, liked in load_profiles().items()]


@app.get("/api/profiles/{user_id}")
def get_profile(user_id: str):
    profiles = load_profiles()
    if user_id not in profiles:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"id": user_id, "liked_book_ids": profiles[user_id], "synthetic": True}


@app.post("/api/recommendations/personalized", response_model=PersonalizedResponse)
def get_personalized_recommendations(request: PersonalizedRequest):
    return personalized_recommendations(request)


# After `npm run build`, one FastAPI process can serve the existing Vite UI.
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"
if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
