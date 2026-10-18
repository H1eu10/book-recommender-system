from app.schemas import (
    Book,
    RecommendationRequest,
    RecommendationResult,
)


def recommend_books(
    books: list[Book],
    preferences: RecommendationRequest,
) -> list[RecommendationResult]:
    results: list[RecommendationResult] = []

    preferred_genres = set(preferences.genres)
    preferred_tags = set(preferences.tags)

    for book in books:
        # Apply mandatory conditions.
        if preferences.language is not None:
            if book.language.strip().lower() != preferences.language:
                continue

        if preferences.max_pages is not None:
            if book.pages is None or book.pages > preferences.max_pages:
                continue

        book_genres = {
            genre.strip().lower() for genre in book.genres
        }
        book_tags = {
            tag.strip().lower() for tag in book.tags
        }

        matched_genres = preferred_genres & book_genres
        matched_tags = preferred_tags & book_tags

        weighted_score = 0.0
        total_weight = 0.0
        reasons: list[str] = []

        if preferred_genres:
            genre_score = len(matched_genres) / len(preferred_genres)
            weighted_score += 0.7 * genre_score
            total_weight += 0.7

        if preferred_tags:
            tag_score = len(matched_tags) / len(preferred_tags)
            weighted_score += 0.3 * tag_score
            total_weight += 0.3

        score = weighted_score / total_weight

        # Do not recommend books with no matching preferences.
        if score <= 0:
            continue

        if matched_genres:
            reasons.append(
                "Matches your preferred genres: "
                + ", ".join(sorted(matched_genres))
                + "."
            )

        if matched_tags:
            reasons.append(
                "Matches your preferred topics: "
                + ", ".join(sorted(matched_tags))
                + "."
            )

        results.append(
            RecommendationResult(
                book=book,
                score=score,
                reasons=reasons,
            )
        )

    results.sort(key=lambda result: (-result.score, result.book.id))

    return results[:preferences.limit]