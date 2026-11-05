from app.schemas import Book, RecommendationResult
from app.content_based import get_index
from app.item_cf import get_item_cf_recommendations 
from typing import Sequence

def get_hybrid_recommendations(
    books: Sequence[Book], user_id: str, genres: list[str], tags: list[str],
    users_data: dict, limit: int = 10, alpha: float = 0.3
) -> list[RecommendationResult]:
    if not 0 <= alpha <= 1 or limit < 1:
        raise ValueError("alpha must be in [0, 1] and limit must be positive")
    seen = set(users_data.get(user_id, []))
    cbf_index = get_index(books)
    cbf_results = [r for r in cbf_index.by_preferences(
        genres=genres, tags=tags, limit=len(books)
    ) if r.book.id not in seen]
    
    cf_results = get_item_cf_recommendations(
        target_user_id=user_id, 
        users_data=users_data, 
        limit=len(books)
    )
    
    merged = {}
    max_cbf_score = max((r.score for r in cbf_results), default=1.0) or 1.0
    for res in cbf_results:
        merged[res.book.id] = {
            "book": res.book, "cbf": res.score / max_cbf_score, "cf": 0.0, "reasons": list(res.reasons)
        }
        
    max_cf_score = max((r["score"] for r in cf_results), default=1.0) or 1.0
    book_dict = {b.id: b for b in books}
    for r in cf_results:
        bid = r["book_id"]
        norm_cf = r["score"] / max_cf_score
        if bid in merged:
            merged[bid]["cf"] = norm_cf
            merged[bid]["reasons"].append("Độc giả quan tâm đến cuốn sách này cũng thích cuốn kia.")
        elif bid in book_dict:
            merged[bid] = {
                "book": book_dict[bid], "cbf": 0.0, "cf": norm_cf,
                "reasons": ["Độc giả quan tâm đến cuốn sách này cũng thích cuốn kia."]
            }

    final_results = []
    for bid, data in merged.items():
        hybrid_score = (alpha * data["cbf"]) + ((1 - alpha) * data["cf"])
        if bid in seen or hybrid_score <= 0:
            continue
        final_results.append(RecommendationResult(
            book=data["book"], score=min(hybrid_score, 1.0), reasons=data["reasons"]
        ))
        
    final_results.sort(key=lambda x: (-x.score, x.book.id))
    return final_results[:limit]
