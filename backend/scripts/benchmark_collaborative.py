"""Compare collaborative models with fixed splits and validation-only selection."""
import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import statistics
import sys
import time

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import torch

from app.collaborative import ItemCFRecommender, PopularityRecommender
from app.collaborative_training import TrainingConfig, train_model
from app.interaction_data import InteractionData, clean_interactions, kfold_splits, split_interactions
from app.ranking_metrics import evaluate

ROOT = BACKEND_ROOT.parent


def positive_int(value):
    value = int(value)
    if value < 1:
        raise argparse.ArgumentTypeError("Must be a positive integer")
    return value


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--books", type=Path, default=ROOT / "data/books.sample.json")
    parser.add_argument("--interactions", type=Path, default=ROOT / "data/user_interactions.json")
    parser.add_argument("--output", type=Path, default=BACKEND_ROOT / "artifacts/collaborative")
    parser.add_argument("--models", nargs="+", choices=["popularity", "itemcf", "ncf", "lightgcn"],
                        default=["popularity", "itemcf", "ncf", "lightgcn"])
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44])
    parser.add_argument("--embedding-dims", nargs="+", type=positive_int, default=[32])
    parser.add_argument("--layers", nargs="+", type=int, default=[2])
    parser.add_argument("--epochs", type=positive_int, default=100)
    parser.add_argument("--patience", type=positive_int, default=10)
    parser.add_argument("--batch-size", type=positive_int, default=2048)
    parser.add_argument("--learning-rate", type=float, default=0.001)
    parser.add_argument("--regularization", type=float, default=0.0001)
    parser.add_argument("--k", type=positive_int, default=10)
    parser.add_argument("--threads", type=positive_int, default=1)
    parser.add_argument("--folds", type=positive_int, default=1,
                        help="1: 60/20/20 holdout; >=3: rotating test/validation folds")
    args = parser.parse_args(argv)
    if args.folds == 2 or any(layer < 0 for layer in args.layers):
        parser.error("Use folds=1 or folds>=3, and nonnegative layer counts")
    if len(set(args.seeds)) != len(args.seeds) or len(set(args.models)) != len(args.models):
        parser.error("Seeds and model names must be unique")
    return args


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args(argv)
    torch.set_num_threads(args.threads)
    base_config = TrainingConfig(epochs=args.epochs, patience=args.patience,
                                 batch_size=args.batch_size, learning_rate=args.learning_rate,
                                 regularization=args.regularization)
    base_config.validate()
    catalog = json.loads(args.books.read_text(encoding="utf-8"))
    item_ids = [book["id"] for book in catalog]
    if len(item_ids) != len(set(item_ids)):
        raise ValueError("Duplicate book IDs in catalog")
    users = clean_interactions(json.loads(args.interactions.read_text(encoding="utf-8")), item_ids)
    dataset_hash = hashlib.sha256(json.dumps(users, sort_keys=True).encode()).hexdigest()
    report = {
        "protocol": "Train-only warm candidates; validation selects config/epoch; test evaluated once per selected model.",
        "data_note": "Bundled user interactions are synthetic, not real reader behavior.",
        "dataset_sha256": dataset_hash,
        "data": {"users": len(users), "catalog_items": len(item_ids),
                 "interactions": sum(map(len, users.values()))},
        "arguments": {key: str(value) if isinstance(value, Path) else value
                      for key, value in vars(args).items()},
        "versions": {"python": sys.version, "torch": torch.__version__},
        "runs": [],
    }
    for seed in args.seeds:
        splits = ([split_interactions(users, seed)] if args.folds == 1
                  else kfold_splits(users, args.folds, seed))
        for fold, split in enumerate(splits):
            data = InteractionData(split.train)
            directory = args.output / f"seed-{seed}" / f"fold-{fold}"
            write_json(directory / "split.json", split.to_dict())
            for kind in args.models:
                start = time.perf_counter()
                trials = []
                if kind in ("popularity", "itemcf"):
                    predictor = (PopularityRecommender if kind == "popularity" else ItemCFRecommender)(data)
                    training = {"training_seconds": time.perf_counter() - start}
                else:
                    best_score = -1.0
                    for dim in args.embedding_dims:
                        for layers in (args.layers if kind == "lightgcn" else [0]):
                            config = replace(base_config, embed_dim=dim, layers=layers, seed=seed)
                            candidate, details = train_model(kind, data, split.validation, config, args.k)
                            trials.append(details)
                            if details["best_validation_ndcg"] > best_score:
                                predictor, training = candidate, details
                                best_score = details["best_validation_ndcg"]
                    predictor.save(directory / f"{kind}.pt", {
                        "split_sha256": split.fingerprint, "dataset_sha256": dataset_hash,
                        "best_epoch": training["best_epoch"], "k": args.k,
                        "purpose": "Evaluation checkpoint fitted to training edges only",
                    })
                validation = evaluate(predictor, split.validation, args.k)
                # Validation positives are known at final evaluation and masked for ALL models.
                test = evaluate(predictor, split.test, args.k, exclude=split.validation)
                run = {"model": kind, "seed": seed, "fold": fold,
                       "split_sha256": split.fingerprint,
                       "train_items": len(data.item_ids), "catalog_cold_items": len(item_ids) - len(data.item_ids),
                       "validation": validation, "test": test, "training": training,
                       "trials": trials, "total_seconds": time.perf_counter() - start}
                report["runs"].append(run)
                print(f"seed={seed} fold={fold} {kind:10} "
                      f"Recall@{args.k}={test[f'recall@{args.k}']:.4f} "
                      f"NDCG@{args.k}={test[f'ndcg@{args.k}']:.4f}", flush=True)
                write_json(args.output / "report.json", report)
    summary = {}
    for kind in args.models:
        selected = [run for run in report["runs"] if run["model"] == kind]
        summary[kind] = {}
        # Average folds within a seed first; seeds are the repeat unit for SD.
        for metric in (f"precision@{args.k}", f"recall@{args.k}", f"ndcg@{args.k}"):
            values = [statistics.mean(run["test"][metric] for run in selected if run["seed"] == seed)
                      for seed in args.seeds]
            summary[kind][metric] = {"mean": statistics.mean(values),
                                     "std": statistics.stdev(values) if len(values) > 1 else 0.0,
                                     "seeds": len(values)}
    report["summary"] = summary
    write_json(args.output / "report.json", report)
    print(f"Report: {(args.output / 'report.json').resolve()}", flush=True)
    return report


if __name__ == "__main__":
    main()
