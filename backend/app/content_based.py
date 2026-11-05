"""Content-based book recommendations using TF-IDF + cosine similarity.

Modes:
    - similar(book_id):  item-to-item ("find books like this one").
    - by_preferences(genres, tags, ...): query from user preferences.

Index is cached in memory and rebuilt when book content or metadata changes.
"""

from __future__ import annotations

import logging
from typing import Sequence

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.schemas import Book, RecommendationResult

logger = logging.getLogger(__name__)


def _weighted_text(book: Book) -> str:
    """Combine text signals with field repetition to bias TF-IDF weights.

    Title (3x) and genres/tags (2x) are the strongest signals; description
    adds longer context. L2 normalization inside TF-IDF keeps long
    descriptions from dominating.
    """
    return " ".join([
        book.title, book.title, book.title,
        " ".join(book.genres), " ".join(book.genres),
        " ".join(book.tags), " ".join(book.tags),
        book.author,
        book.description or "",
    ])


class ContentBasedIndex:
    """Pre-computed TF-IDF matrix over a fixed book corpus."""

    def __init__(self, books: Sequence[Book]) -> None:
        self.books = list(books)
        self._id_to_pos = {b.id: i for i, b in enumerate(self.books)}

        texts = [_weighted_text(b) for b in self.books]
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=1,
            sublinear_tf=True,
            stop_words="english",
        )
        self.matrix = self.vectorizer.fit_transform(texts)
        logger.info(
            "ContentBasedIndex built: %d books, %d features",
            len(self.books), self.matrix.shape[1],
        )

    # -- item-to-item -------------------------------------------------------

    def similar(self, book_id: str, limit: int = 10) -> list[RecommendationResult]:
        if book_id not in self._id_to_pos:
            logger.warning("similar(): unknown book_id=%r", book_id)
            return []

        pos = self._id_to_pos[book_id]
        sims = cosine_similarity(self.matrix[pos], self.matrix)[0]
        sims[pos] = -1.0  # exclude the query book itself

        top_idx = np.argsort(sims)[::-1][:limit]
        query = self.books[pos]
        results: list[RecommendationResult] = []
        for idx in top_idx:
            score = float(sims[idx])
            if score <= 0:
                continue
            candidate = self.books[idx]
            results.append(RecommendationResult(
                book=candidate,
                score=min(score, 1.0),
                reasons=self._explain(query, candidate),
            ))
        return results

    # -- preference query ---------------------------------------------------

    def by_preferences(
        self,
        genres: Sequence[str],
        tags: Sequence[str] = (),
        language: str | None = None,
        max_pages: int | None = None,
        limit: int = 10,
    ) -> list[RecommendationResult]:
        query_text = " ".join([
            " ".join(genres), " ".join(genres),
            " ".join(tags), " ".join(tags),
        ]).strip()
        if not query_text:
            return []

        query_vec = self.vectorizer.transform([query_text])
        sims = cosine_similarity(query_vec, self.matrix)[0]

        # Mandatory filters: zero out disqualified rows.
        for i, book in enumerate(self.books):
            if language and book.language.lower() != language.lower():
                sims[i] = 0.0
            if max_pages is not None and (
                book.pages is None or book.pages > max_pages
            ):
                sims[i] = 0.0

        top_idx = np.argsort(sims)[::-1][:limit]
        wanted_genres = {g.lower() for g in genres}
        wanted_tags = {t.lower() for t in tags}

        results: list[RecommendationResult] = []
        for idx in top_idx:
            score = float(sims[idx])
            if score <= 0:
                continue
            candidate = self.books[idx]
            matched_g = sorted(
                wanted_genres & {g.lower() for g in candidate.genres}
            )
            matched_t = sorted(
                wanted_tags & {t.lower() for t in candidate.tags}
            )
            reasons: list[str] = []
            if matched_g:
                reasons.append(f"Matches genres: {', '.join(matched_g)}.")
            if matched_t:
                reasons.append(f"Matches themes: {', '.join(matched_t)}.")
            results.append(RecommendationResult(
                book=candidate,
                score=min(score, 1.0),
                reasons=reasons,
            ))
        return results

    # -- explanations -------------------------------------------------------

    @staticmethod
    def _explain(query: Book, candidate: Book) -> list[str]:
        reasons: list[str] = []
        shared_g = sorted(
            {g.lower() for g in query.genres}
            & {g.lower() for g in candidate.genres}
        )
        if shared_g:
            reasons.append(f"Shares genres: {', '.join(shared_g)}.")
        shared_t = sorted(
            {t.lower() for t in query.tags}
            & {t.lower() for t in candidate.tags}
        )
        if shared_t:
            reasons.append(f"Shares themes: {', '.join(shared_t[:5])}.")
        return reasons


# ---------------------------------------------------------------------------
# Index cache
# ---------------------------------------------------------------------------

_INDEX: ContentBasedIndex | None = None
_INDEX_KEY: tuple[str, ...] | None = None


def get_index(books: Sequence[Book]) -> ContentBasedIndex:
    """Rebuild when book content or metadata changes, even if IDs stay the same."""
    global _INDEX, _INDEX_KEY
    key = tuple(b.model_dump_json() for b in books)
    if _INDEX is None or _INDEX_KEY != key:
        _INDEX = ContentBasedIndex(books)
        _INDEX_KEY = key
    return _INDEX
