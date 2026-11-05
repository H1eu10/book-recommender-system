"""CPU training, validation selection and portable inference checkpoints."""
from copy import deepcopy
from dataclasses import asdict, dataclass
from pathlib import Path
import random
import time

import numpy as np
import torch
from torch.nn import functional as F

from app.collaborative import PopularityRecommender
from app.interaction_data import InteractionData
from app.lightgcn import LightGCN, normalized_graph
from app.ncf import NCF
from app.ranking_metrics import evaluate


@dataclass
class TrainingConfig:
    embed_dim: int = 32
    layers: int = 2
    epochs: int = 100
    batch_size: int = 2048
    learning_rate: float = 0.001
    regularization: float = 0.0001
    patience: int = 10
    seed: int = 42

    def validate(self):
        if min(self.embed_dim, self.epochs, self.batch_size, self.patience) < 1:
            raise ValueError("Dimensions, epochs, batch size and patience must be positive")
        if self.layers < 0 or self.learning_rate <= 0 or self.regularization < 0:
            raise ValueError("Invalid layers, learning rate or regularization")


def seed_everything(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.use_deterministic_algorithms(True)


def make_model(kind, data, config):
    if kind == "lightgcn":
        return LightGCN(len(data.user_ids), len(data.item_ids), normalized_graph(data),
                        config.embed_dim, config.layers)
    if kind == "ncf":
        return NCF(len(data.user_ids), len(data.item_ids), config.embed_dim)
    raise ValueError(f"Unsupported neural model: {kind}")


class NeuralRecommender(PopularityRecommender):
    def __init__(self, data, model, kind, config):
        super().__init__(data)
        self.model = model.cpu().eval()
        self.kind, self.config = kind, config
        self._score_cache = {}
        with torch.no_grad():
            self._vectors = model.propagate() if kind == "lightgcn" else None

    def scores(self, user_id):
        idx = self.data.user_to_idx.get(user_id)
        if idx is None or self.data.matrix[idx].nnz == 0:
            return super().scores(user_id)
        if user_id not in self._score_cache:
            with torch.no_grad():
                if self._vectors is not None:
                    users, items = self._vectors
                    scores = items @ users[idx]
                else:
                    item_ids = torch.arange(len(self.data.item_ids))
                    user_ids = torch.full_like(item_ids, idx)
                    scores = self.model(user_ids, item_ids)
                self._score_cache[user_id] = scores.numpy().copy()
        return self._score_cache[user_id].copy()

    def save(self, path, metadata=None):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save({"format_version": 1, "kind": self.kind,
                    "config": asdict(self.config), "train": self.data.train,
                    "user_ids": self.data.user_ids, "item_ids": self.data.item_ids,
                    "state_dict": self.model.state_dict(), "metadata": metadata or {}}, path)

    @classmethod
    def load(cls, path):
        payload = torch.load(path, map_location="cpu", weights_only=True)
        if payload.get("format_version") != 1:
            raise ValueError("Unsupported checkpoint format")
        data = InteractionData(payload["train"])
        if data.user_ids != payload["user_ids"] or data.item_ids != payload["item_ids"]:
            raise ValueError("Checkpoint ID mappings do not match training interactions")
        config = TrainingConfig(**payload["config"])
        config.validate()
        model = make_model(payload["kind"], data, config)
        model.load_state_dict(payload["state_dict"], strict=True)
        return cls(data, model, payload["kind"], config)


class BPRSampler:
    """Fresh negatives each epoch, drawn only using training information.

    Explicit complement pools avoid infinite rejection loops for saturated users.
    A missing interaction is unobserved, not a confirmed dislike.
    """
    def __init__(self, data, seed):
        self.rng = np.random.default_rng(seed)
        all_items = np.arange(len(data.item_ids))
        self.pools, pairs = {}, []
        for user in range(len(data.user_ids)):
            positive = data.matrix[user].indices
            negatives = np.setdiff1d(all_items, positive)
            if len(positive) and len(negatives):
                self.pools[user] = negatives
                pairs.extend((user, int(item)) for item in positive)
        if not pairs:
            raise ValueError("BPR requires a user with both observed and unobserved items")
        self.pairs = np.asarray(pairs, dtype=np.int64)

    def epoch(self):
        pairs = self.pairs[self.rng.permutation(len(self.pairs))]
        negatives = np.asarray([self.rng.choice(self.pools[int(user)]) for user in pairs[:, 0]])
        return torch.from_numpy(np.column_stack((pairs, negatives)))


def train_model(kind, data, validation, config, k=10):
    config.validate()
    seed_everything(config.seed)
    model = make_model(kind, data, config)
    sampler = BPRSampler(data, config.seed)
    # LightGCN uses explicit regularization on sampled layer-zero embeddings.
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate,
                                 weight_decay=config.regularization if kind == "ncf" else 0)
    best_score, best_state, best_epoch, stale = -1.0, None, 0, 0
    history = []
    start = time.perf_counter()
    for epoch in range(1, config.epochs + 1):
        model.train()
        triples = sampler.epoch()
        loss_sum = 0.0
        for batch in triples.split(config.batch_size):
            users, positive, negative = batch.unbind(dim=1)
            optimizer.zero_grad()
            if kind == "lightgcn":
                pos, neg = model.pairwise_scores(users, positive, negative)
                penalty = config.regularization * model.regularization(users, positive, negative)
            else:
                pos, neg = model(users, positive), model(users, negative)
                penalty = 0.0
            loss = F.softplus(neg - pos).mean() + penalty
            if not torch.isfinite(loss):
                raise RuntimeError("Non-finite BPR training loss")
            loss.backward()
            optimizer.step()
            loss_sum += float(loss.detach()) * len(batch)
        predictor = NeuralRecommender(data, model, kind, config)
        metrics = evaluate(predictor, validation, k)
        score = metrics[f"ndcg@{k}"]
        history.append({"epoch": epoch, "loss": loss_sum / len(triples),
                        "validation": metrics})
        if score > best_score:
            best_score, best_epoch = score, epoch
            best_state, stale = deepcopy(model.state_dict()), 0
        else:
            stale += 1
        if stale >= config.patience:
            break
    model.load_state_dict(best_state)
    return NeuralRecommender(data, model, kind, config), {
        "best_epoch": best_epoch, "best_validation_ndcg": best_score,
        "training_seconds": time.perf_counter() - start, "history": history,
        "config": asdict(config)}
