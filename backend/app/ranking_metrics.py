"""Macro ranking metrics; every model is evaluated on the same warm catalog."""
import math


def ranking_metrics(recommended, relevant, k):
    if k < 1:
        raise ValueError("k must be positive")
    relevant = set(relevant)
    top = list(recommended)[:k]
    if len(top) != len(set(top)):
        raise ValueError("Recommendations must be unique")
    hits = len(set(top) & relevant)
    dcg = sum(1 / math.log2(i + 2) for i, b in enumerate(top) if b in relevant)
    ideal = sum(1 / math.log2(i + 2) for i in range(min(k, len(relevant))))
    return {f"precision@{k}": hits / k,
            f"recall@{k}": hits / len(relevant) if relevant else 0.0,
            f"ndcg@{k}": dcg / ideal if ideal else 0.0}


def evaluate(model, targets, k=10, exclude=None):
    catalog = set(model.data.item_ids)
    totals = {f"{name}@{k}": 0.0 for name in ("precision", "recall", "ndcg")}
    users_evaluated = cold_targets = target_count = users_without_warm_targets = 0
    for user in sorted(targets):
        held_out = set(targets[user])
        target_count += len(held_out)
        cold_targets += len(held_out - catalog)
        relevant = held_out & catalog
        if not relevant:
            users_without_warm_targets += bool(held_out)
            continue
        blocked = (exclude or {}).get(user, ())
        if relevant & (set(model.data.train.get(user, ())) | set(blocked)):
            raise ValueError("Held-out targets overlap seen or excluded items")
        recs = model.recommend(user, k, exclude=blocked)
        scores = ranking_metrics([r["book_id"] for r in recs], relevant, k)
        for key, value in scores.items():
            totals[key] += value
        users_evaluated += 1
    if not users_evaluated:
        raise ValueError("No users with warm held-out targets to evaluate")
    return {**{key: value / users_evaluated for key, value in totals.items()},
            "users_evaluated": users_evaluated,
            "held_out_interactions": target_count,
            "cold_item_targets_excluded": cold_targets,
            "users_without_warm_targets": users_without_warm_targets}
