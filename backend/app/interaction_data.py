"""Deterministic implicit-feedback splits. Held-out edges never enter training."""
from dataclasses import asdict, dataclass
import hashlib
import json
import random

import numpy as np
from scipy.sparse import csr_matrix


@dataclass
class InteractionSplit:
    train: dict[str, list[str]]
    validation: dict[str, list[str]]
    test: dict[str, list[str]]
    seed: int

    def to_dict(self):
        return asdict(self)

    @property
    def fingerprint(self):
        payload = json.dumps(self.to_dict(), sort_keys=True).encode()
        return hashlib.sha256(payload).hexdigest()


def clean_interactions(users, catalog=None):
    allowed = set(catalog) if catalog is not None else None
    result = {}
    for user in sorted(users):
        liked = users[user]
        if not isinstance(user, str) or not isinstance(liked, list):
            raise ValueError("Interactions must map string user IDs to lists of book IDs")
        if any(not isinstance(book, str) for book in liked):
            raise ValueError("Book IDs must be strings")
        if allowed is not None and set(liked) - allowed:
            raise ValueError(f"Unknown catalog book IDs for {user}")
        result[user] = sorted(set(liked))
    return result


def split_interactions(users, seed=42, validation_ratio=0.2, test_ratio=0.2):
    if not (0 < validation_ratio < 1 and 0 < test_ratio < 1
            and validation_ratio + test_ratio < 1):
        raise ValueError("Validation and test ratios must be positive and sum to < 1")
    rng = random.Random(seed)
    train, validation, test = {}, {}, {}
    for user, liked in clean_interactions(users).items():
        rng.shuffle(liked)
        # Sparse users remain training-only: at least one training edge is required.
        if len(liked) < 3:
            train[user], validation[user], test[user] = sorted(liked), [], []
            continue
        n_test = min(max(1, int(len(liked) * test_ratio)), len(liked) - 2)
        n_val = min(max(1, int(len(liked) * validation_ratio)), len(liked) - n_test - 1)
        test[user] = sorted(liked[:n_test])
        validation[user] = sorted(liked[n_test:n_test + n_val])
        train[user] = sorted(liked[n_test + n_val:])
    return InteractionSplit(train, validation, test, seed)


def kfold_splits(users, folds=5, seed=42):
    """Shuffle once; disjoint test folds, next fold validation, remainder train.

    Users with fewer than `folds` interactions contribute training data only.
    """
    if folds < 3:
        raise ValueError("At least three folds are needed for train/validation/test")
    rng = random.Random(seed)
    partitions, training_only = {}, {}
    for user, liked in clean_interactions(users).items():
        rng.shuffle(liked)
        if len(liked) < folds:
            training_only[user] = sorted(liked)
        else:
            partitions[user] = [sorted(liked[i::folds]) for i in range(folds)]
    for fold in range(folds):
        train = {u: list(v) for u, v in training_only.items()}
        validation = {u: [] for u in training_only}
        test = {u: [] for u in training_only}
        for user, parts in partitions.items():
            test[user] = parts[fold]
            validation[user] = parts[(fold + 1) % folds]
            train[user] = sorted(b for i, part in enumerate(parts)
                                 if i not in (fold, (fold + 1) % folds) for b in part)
        yield InteractionSplit(train, validation, test, seed)


class InteractionData:
    """Stable mappings and a binary CSR user-item matrix built from TRAIN only."""
    def __init__(self, train):
        self.train = clean_interactions(train)
        self.user_ids = sorted(self.train)
        self.item_ids = sorted({b for liked in self.train.values() for b in liked})
        if not self.user_ids or not self.item_ids:
            raise ValueError("Training data must contain at least one interaction")
        self.user_to_idx = {u: i for i, u in enumerate(self.user_ids)}
        self.item_to_idx = {b: i for i, b in enumerate(self.item_ids)}
        rows, cols = [], []
        for user, liked in self.train.items():
            rows.extend([self.user_to_idx[user]] * len(liked))
            cols.extend(self.item_to_idx[b] for b in liked)
        self.matrix = csr_matrix((np.ones(len(rows), dtype=np.float32), (rows, cols)),
                                 shape=(len(self.user_ids), len(self.item_ids)))

    def rank(self, scores, user_id, limit=10, exclude=()):
        if limit < 1:
            raise ValueError("limit must be positive")
        scores = np.asarray(scores, dtype=float).reshape(-1)
        if len(scores) != len(self.item_ids) or not np.isfinite(scores).all():
            raise ValueError("Expected one finite score per training item")
        blocked = set(self.train.get(user_id, ())) | set(exclude)
        candidates = [i for i, book in enumerate(self.item_ids) if book not in blocked]
        # Item ID breaks ties consistently across models and runs.
        candidates.sort(key=lambda i: (-scores[i], self.item_ids[i]))
        return [{"book_id": self.item_ids[i], "score": float(scores[i])}
                for i in candidates[:limit]]
