"""Load a trained checkpoint and rank unread books without retraining."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.collaborative_training import NeuralRecommender


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("user_id")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--exclude", nargs="*", default=[], help="Additional known book IDs")
    args = parser.parse_args()
    model = NeuralRecommender.load(args.checkpoint)
    print(json.dumps({"model": model.kind,
                      "fallback": args.user_id not in model.data.user_to_idx
                                  or not model.data.train.get(args.user_id),
                      "recommendations": model.recommend(args.user_id, args.limit, args.exclude)},
                     indent=2))


if __name__ == "__main__":
    main()
