"""Application adapters for existing recommenders; never trains in an API request."""
from functools import lru_cache
from importlib.util import find_spec
import json
import logging
import os
import pickle
from pathlib import Path

from fastapi import HTTPException

from app.book_service import PROJECT_ROOT, load_books
from app.schemas import PersonalizedResponse, PersonalizedResult, RecommendationExplanation

logger = logging.getLogger(__name__)
USERS_FILE = PROJECT_ROOT / "data" / "user_interactions.json"
MODEL_IDS = ("popularity", "itemcf", "ncf", "lightgcn")


def checkpoint_path(model):
    default = PROJECT_ROOT / "backend/artifacts/collaborative/seed-42/fold-0"
    return Path(os.environ.get("BOOK_MODEL_DIR", str(default))) / f"{model}.pt"


@lru_cache(maxsize=4)
def _read_profiles(stamp):
    from app.interaction_data import clean_interactions
    return clean_interactions(json.loads(USERS_FILE.read_text(encoding="utf-8")),
                              [book.id for book in load_books()])


def load_profiles():
    try:
        stat = USERS_FILE.stat()
        return _read_profiles((stat.st_mtime_ns, stat.st_size))
    except (OSError, ValueError, TypeError, KeyError):
        logger.exception("Cannot load demo profiles")
        raise HTTPException(status_code=503, detail="Profiles unavailable") from None


def available_models():
    return [{"id": model, "available": model in ("popularity", "itemcf")
             or (find_spec("torch") is not None and checkpoint_path(model).is_file())} for model in MODEL_IDS]


@lru_cache(maxsize=4)
def _baseline(model, stamp):
    from app.collaborative import ItemCFRecommender, PopularityRecommender
    from app.interaction_data import InteractionData
    data = InteractionData(load_profiles())
    return (ItemCFRecommender if model == "itemcf" else PopularityRecommender)(data)


@lru_cache(maxsize=4)
def _checkpoint(path, stamp):
    from app.collaborative_training import NeuralRecommender
    return NeuralRecommender.load(path)


def personalized_recommendations(request):
    profiles = load_profiles()
    if request.user_id not in profiles:
        raise HTTPException(status_code=404, detail="Profile not found")
    try:
        if request.model in ("popularity", "itemcf"):
            model = _baseline(request.model, USERS_FILE.stat().st_mtime_ns)
        else:
            path = checkpoint_path(request.model)
            model = _checkpoint(str(path.resolve()), path.stat().st_mtime_ns)
            if model.kind != request.model:
                raise ValueError("Checkpoint model kind mismatch")
    except (OSError, ValueError, RuntimeError, KeyError, ImportError, pickle.UnpicklingError, EOFError, TypeError):
        logger.exception("Recommendation model unavailable: %s", request.model)
        raise HTTPException(status_code=503, detail="Model unavailable") from None
    fallback = not model.data.train.get(request.user_id)
    # Evaluation checkpoints only know train likes. Mask the entire visible profile
    # (including held-out likes) when serving this demo, without fitting any new edges.
    catalog = {book.id: book for book in load_books()}
    exclude = set(profiles[request.user_id]) | (set(model.data.item_ids) - set(catalog))
    results = model.recommend(request.user_id, request.limit, exclude=exclude)
    code = "popularity" if fallback or request.model == "popularity" else "history"
    return PersonalizedResponse(model=request.model, fallback=fallback, results=[
        PersonalizedResult(book=catalog[row["book_id"]], score=row["score"],
                           explanations=[RecommendationExplanation(code=code)])
        for row in results
    ])
