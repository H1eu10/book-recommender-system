"""LightGCN (He et al., SIGIR 2020): normalized propagation and layer averaging.

Reference: https://arxiv.org/abs/2002.02126
No self-loops, feature transforms or nonlinear activations in propagation.
"""
import numpy as np
from scipy.sparse import bmat, diags
import torch
from torch import nn

from app.interaction_data import InteractionData


def normalized_graph(data: InteractionData):
    adjacency = bmat([[None, data.matrix], [data.matrix.T, None]], format="coo")
    degree = np.asarray(adjacency.sum(axis=1)).ravel()
    inverse = np.zeros_like(degree)
    np.divide(1.0, np.sqrt(degree), out=inverse, where=degree > 0)
    graph = (diags(inverse) @ adjacency @ diags(inverse)).tocoo()
    indices = torch.from_numpy(np.vstack((graph.row, graph.col)).astype(np.int64))
    values = torch.from_numpy(graph.data.astype(np.float32))
    return torch.sparse_coo_tensor(indices, values, graph.shape, check_invariants=True).coalesce()


class LightGCN(nn.Module):
    def __init__(self, num_users, num_items, graph, embed_dim=32, layers=2):
        super().__init__()
        if num_users < 1 or num_items < 1 or embed_dim < 1 or layers < 0:
            raise ValueError("Invalid LightGCN dimensions or layer count")
        if tuple(graph.shape) != (num_users + num_items,) * 2:
            raise ValueError("Graph shape does not match the ID mappings")
        self.num_users = num_users
        self.layers = layers
        self.embedding = nn.Embedding(num_users + num_items, embed_dim)
        nn.init.normal_(self.embedding.weight, std=0.1)
        self.register_buffer("graph", graph.coalesce(), persistent=False)

    def propagate(self):
        current = self.embedding.weight
        combined = current
        for _ in range(self.layers):
            current = torch.sparse.mm(self.graph, current)
            combined = combined + current
        combined = combined / (self.layers + 1)  # includes layer zero
        return combined[:self.num_users], combined[self.num_users:]

    def forward(self, users, items):
        user_vectors, item_vectors = self.propagate()
        return (user_vectors[users] * item_vectors[items]).sum(dim=-1)

    def pairwise_scores(self, users, positive, negative):
        user_vectors, item_vectors = self.propagate()
        return ((user_vectors[users] * item_vectors[positive]).sum(dim=-1),
                (user_vectors[users] * item_vectors[negative]).sum(dim=-1))

    def regularization(self, users, positive, negative):
        # Regularize trainable layer-zero embeddings, not propagated embeddings.
        return (self.embedding(users).square().sum()
                + self.embedding(positive + self.num_users).square().sum()
                + self.embedding(negative + self.num_users).square().sum()) / (2 * len(users))
