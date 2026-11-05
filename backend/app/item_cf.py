"""Backward-compatible Item-CF entry point; fit-once class for benchmarks."""
from app.collaborative import ItemCFRecommender
from app.interaction_data import InteractionData


def get_item_cf_recommendations(target_user_id: str, users_data: dict, limit: int = 5):
    if limit < 1:
        raise ValueError("limit must be positive")
    if not users_data.get(target_user_id):
        return []
    model = ItemCFRecommender(InteractionData(users_data))
    return [r for r in model.recommend(target_user_id, limit) if r["score"] > 0]
