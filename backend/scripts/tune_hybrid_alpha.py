"""Legacy TF-IDF/Item-CF hybrid: tune alpha on validation, evaluate test once."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from app.book_service import load_books
from app.collaborative import ItemCFRecommender
from app.content_based import get_index
from app.interaction_data import InteractionData, split_interactions
from app.ranking_metrics import evaluate

ROOT = Path(__file__).resolve().parents[2]


class ContentHybrid(ItemCFRecommender):
    def __init__(self, data, books):
        super().__init__(data)
        self.alpha = 0.0
        self.content_scores = {}
        index = get_index(books)
        positions = {book.id: i for i, book in enumerate(books)}
        for user, liked in data.train.items():
            # Average only the training-liked content vectors; no held-out metadata query.
            if not liked:
                self.content_scores[user] = np.zeros(len(data.item_ids))
                continue
            profile = np.asarray(index.matrix[[positions[bid] for bid in liked]].mean(axis=0))
            self.content_scores[user] = cosine_similarity(
                profile, index.matrix[[positions[bid] for bid in data.item_ids]]
            ).ravel()

    def scores(self, user_id):
        cf = super().scores(user_id)
        cbf = self.content_scores.get(user_id, np.zeros_like(cf))
        return (self.alpha * cbf / (cbf.max() or 1.0)
                + (1 - self.alpha) * cf / (cf.max() or 1.0))


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--output", type=Path, default=ROOT / "backend/artifacts/hybrid/report.json")
    args = parser.parse_args()
    raw = json.loads((ROOT / "data/user_interactions.json").read_text(encoding="utf-8"))
    split = split_interactions(raw, seed=args.seed)
    model = ContentHybrid(InteractionData(split.train), load_books())
    best_alpha, best_score, trials = 0.0, -1.0, []
    for step in range(11):
        model.alpha = step / 10
        metrics = evaluate(model, split.validation, args.k)
        trials.append({"alpha": model.alpha, "validation": metrics})
        if metrics[f"ndcg@{args.k}"] > best_score:
            best_alpha, best_score = model.alpha, metrics[f"ndcg@{args.k}"]
    model.alpha = best_alpha
    report = {"seed": args.seed, "split_sha256": split.fingerprint,
              "note": "Synthetic interactions; content-profile hybrid, separate from the LightGCN benchmark.",
              "alpha": best_alpha, "trials": trials,
              "test": evaluate(model, split.test, args.k, exclude=split.validation)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps(report["test"], indent=2))


if __name__ == "__main__":
    main()
