"""Fit-once baselines sharing the same candidates, masking and tie-breaking."""
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from app.interaction_data import InteractionData


class PopularityRecommender:
    def __init__(self, data: InteractionData):
        self.data = data
        self.popularity = np.asarray(data.matrix.sum(axis=0)).ravel()

    def scores(self, user_id):
        return self.popularity.copy()

    def recommend(self, user_id, limit=10, exclude=()):
        return self.data.rank(self.scores(user_id), user_id, limit, exclude)


class ItemCFRecommender(PopularityRecommender):
    def __init__(self, data):
        super().__init__(data)
        self.similarity = cosine_similarity(data.matrix.T, dense_output=False).tocsr()
        self.similarity.setdiag(0)
        self.similarity.eliminate_zeros()

    def scores(self, user_id):
        user = self.data.user_to_idx.get(user_id)
        if user is None or self.data.matrix[user].nnz == 0:
            return super().scores(user_id)
        return (self.data.matrix[user] @ self.similarity).toarray().ravel()
