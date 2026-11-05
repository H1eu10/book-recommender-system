import math

import numpy as np
import pytest
import torch

from app.collaborative import ItemCFRecommender, PopularityRecommender
from app.collaborative_training import BPRSampler, NeuralRecommender, TrainingConfig, train_model
from app.interaction_data import InteractionData, kfold_splits, split_interactions
from app.lightgcn import LightGCN, normalized_graph
from app.ranking_metrics import evaluate, ranking_metrics


@pytest.fixture
def data():
    return InteractionData({"u": ["a"], "v": ["b", "c"], "w": ["a", "c"], "empty": []})


def test_split_is_order_independent_and_keeps_input_unchanged():
    users = {"z": ["f", "e", "d", "c", "b", "a", "a"], "a": ["x", "y"]}
    split = split_interactions(users)
    reordered = {"a": ["y", "x"], "z": ["a", "b", "c", "d", "e", "f"]}
    assert split.to_dict() == split_interactions(reordered).to_dict()
    assert users["z"].count("a") == 2
    for user, liked in users.items():
        parts = [set(part[user]) for part in (split.train, split.validation, split.test)]
        assert set.union(*parts) == set(liked)
        assert not (parts[0] & parts[1] or parts[0] & parts[2] or parts[1] & parts[2])
        assert parts[0]
    assert split.validation["a"] == split.test["a"] == []


def test_folds_cover_each_eligible_interaction_exactly_once():
    users = {"u": [str(i) for i in range(13)], "sparse": ["0", "1"]}
    splits = list(kfold_splits(users, 5))
    held_out = [book for split in splits for book in split.test["u"]]
    assert sorted(held_out) == sorted(users["u"])
    assert len(held_out) == len(set(held_out))
    for split in splits:
        assert not set(split.test["u"]) & set(split.validation["u"] + split.train["u"])
        assert not set(split.train["u"]) & set(split.validation["u"])
        assert split.test["sparse"] == []


def test_small_split_preserves_validation_even_with_large_test_ratio():
    split = split_interactions({"u": ["a", "b", "c"]}, validation_ratio=0.1, test_ratio=0.8)
    assert all(len(part["u"]) == 1 for part in (split.train, split.validation, split.test))


def test_graph_contains_only_train_edges_with_symmetric_normalization(data):
    graph = normalized_graph(data).to_dense().numpy()
    u = data.user_to_idx["u"]
    a = len(data.user_ids) + data.item_to_idx["a"]
    b = len(data.user_ids) + data.item_to_idx["b"]
    assert graph[u, a] == pytest.approx(1 / math.sqrt(2))
    assert graph[u, b] == 0  # held-out edge must not be injected
    assert np.allclose(graph, graph.T)
    assert np.all(np.diag(graph) == 0)
    assert np.isfinite(graph).all()
    assert not graph[data.user_to_idx["empty"]].any()


def test_lightgcn_averages_zero_and_propagated_layers(data):
    graph = normalized_graph(data)
    model = LightGCN(len(data.user_ids), len(data.item_ids), graph, embed_dim=1, layers=1)
    with torch.no_grad():
        model.embedding.weight.fill_(1.0)
        users, items = model.propagate()
        expected = (torch.ones_like(model.embedding.weight)
                    + torch.sparse.mm(graph, torch.ones_like(model.embedding.weight))) / 2
        assert torch.allclose(torch.cat((users, items)), expected)


def test_sampler_avoids_seen_items_and_handles_saturated_users(data):
    saturated = InteractionData({"full": ["a", "b"], "partial": ["a"]})
    sample = BPRSampler(saturated, 42).epoch()
    assert len(sample) == 1
    for u, p, n in BPRSampler(data, 42).epoch().tolist():
        assert p in data.matrix[u].indices
        assert n not in data.matrix[u].indices
    with pytest.raises(ValueError, match="BPR requires"):
        BPRSampler(InteractionData({"full": ["a"]}), 42)


def test_metrics_known_ranking_and_short_lists():
    result = ranking_metrics(["a", "x", "b"], {"a", "b"}, 3)
    assert result["precision@3"] == pytest.approx(2 / 3)
    assert result["recall@3"] == 1
    assert result["ndcg@3"] == pytest.approx(1.5 / (1 + 1 / math.log2(3)))
    assert ranking_metrics(["a"], {"a"}, 10)["precision@10"] == 0.1


@pytest.mark.parametrize("kind", [PopularityRecommender, ItemCFRecommender])
def test_baseline_masks_seen_and_extra_items_and_handles_cold_user(data, kind):
    model = kind(data)
    assert [r["book_id"] for r in model.recommend("u", exclude=["b"])] == ["c"]
    assert model.recommend("unknown") == PopularityRecommender(data).recommend("unknown")
    assert model.recommend("u", exclude=["b", "c"]) == []


def test_evaluation_reports_cold_targets_and_rejects_leakage(data):
    model = PopularityRecommender(data)
    result = evaluate(model, {"u": ["b", "cold"], "v": ["cold"]}, k=2)
    assert result["users_evaluated"] == 1
    assert result["cold_item_targets_excluded"] == 2
    assert result["users_without_warm_targets"] == 1
    with pytest.raises(ValueError, match="overlap"):
        evaluate(model, {"u": ["a"]})


@pytest.mark.parametrize("kind", ["lightgcn", "ncf"])
def test_training_checkpoint_roundtrip_and_inference(data, kind, tmp_path):
    torch.set_num_threads(1)
    config = TrainingConfig(embed_dim=4, epochs=4, patience=2, batch_size=1)
    validation = {"u": ["b"], "v": ["a"], "w": ["b"]}
    model, details = train_model(kind, data, validation, config, k=2)
    assert 1 <= details["best_epoch"] <= 4
    assert all(math.isfinite(row["loss"]) for row in details["history"])
    path = tmp_path / "model.pt"
    model.save(path, {"split": "test-fixture"})
    restored = NeuralRecommender.load(path)
    for user in ("u", "v", "unknown", "empty"):
        np.testing.assert_array_equal(model.scores(user), restored.scores(user))
        assert restored.recommend(user) == model.recommend(user)
    assert [r["book_id"] for r in restored.recommend("u", exclude=["b"])] == ["c"]
    if kind == "lightgcn":
        again, _ = train_model(kind, data, validation, config, k=2)
        np.testing.assert_array_equal(model.scores("u"), again.scores("u"))


def test_lightgcn_bpr_learns_observed_over_unobserved_items():
    torch.manual_seed(7)
    data = InteractionData({"u": ["a"], "v": ["b"]})
    model = LightGCN(2, 2, normalized_graph(data), embed_dim=4, layers=1)
    users, positive, negative = torch.tensor([0, 1]), torch.tensor([0, 1]), torch.tensor([1, 0])
    optimizer = torch.optim.Adam(model.parameters(), lr=0.05)
    initial = None
    for _ in range(40):
        optimizer.zero_grad()
        pos, neg = model.pairwise_scores(users, positive, negative)
        loss = torch.nn.functional.softplus(neg - pos).mean()
        if initial is None:
            initial = loss.item()
        loss.backward()
        optimizer.step()
    pos, neg = model.pairwise_scores(users, positive, negative)
    assert torch.all(pos > neg + 1)
    assert loss.item() < initial / 10


def test_hybrid_does_not_recommend_seen_books_at_either_alpha_extreme():
    from app.hybrid import get_hybrid_recommendations
    from app.schemas import Book

    books = [Book(id=bid, title=f"Fantasy {bid}", author="Writer", genres=["fantasy"],
                  tags=["magic"], description="A magical quest", language="en")
             for bid in ("a", "b", "c")]
    users = {"u": ["a"], "v": ["a", "b"], "w": ["b", "c"]}
    for alpha in (0.0, 0.5, 1.0):
        recs = get_hybrid_recommendations(books, "u", ["fantasy"], [], users, alpha=alpha)
        assert recs
        assert all(r.book.id != "a" and r.score > 0 for r in recs)
