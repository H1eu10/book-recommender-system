import numpy as np
from sklearn.decomposition import TruncatedSVD
from scipy.sparse import csr_matrix

def get_svd_recommendations(target_user_id: str, users_data: dict, limit: int = 5, n_components: int = 20):
    if target_user_id not in users_data or not users_data[target_user_id]:
        return []

    # 1. Chuẩn bị mapping
    all_books = sorted(list(set(book_id for liked in users_data.values() for book_id in liked)))
    user_ids = list(users_data.keys())
    book_to_idx = {b_id: i for i, b_id in enumerate(all_books)}
    user_to_idx = {u_id: i for i, u_id in enumerate(user_ids)}
    
    num_users, num_books = len(user_ids), len(all_books)
    
    # 2. Tạo ma trận User-Item
    matrix = np.zeros((num_users, num_books))
    for u_id, liked_books in users_data.items():
        u_idx = user_to_idx[u_id]
        for b_id in liked_books:
            if b_id in book_to_idx:
                matrix[u_idx, book_to_idx[b_id]] = 1

    # 3. Áp dụng SVD (Phân rã ma trận)
    # Dùng csr_matrix để tối ưu bộ nhớ cho ma trận thưa
    sparse_matrix = csr_matrix(matrix)
    
    # Số components (yếu tố ẩn) phải nhỏ hơn số user và số sách
    max_comp = min(num_users, num_books) - 1
    actual_comp = min(n_components, max_comp)
    
    svd = TruncatedSVD(n_components=actual_comp, random_state=42)
    
    # Fit và biến đổi ma trận
    user_latent_matrix = svd.fit_transform(sparse_matrix)
    
    # Tái tạo lại ma trận đã được "khử nhiễu" (Reconstructed Matrix)
    # Ma trận này chứa dự đoán mức độ yêu thích (từ 0 đến 1) của user với sách
    reconstructed_matrix = np.dot(user_latent_matrix, svd.components_)

    # 4. Lấy dự đoán cho target_user
    target_idx = user_to_idx[target_user_id]
    user_predictions = reconstructed_matrix[target_idx]
    
    target_liked = users_data[target_user_id]
    recommended_scores = {}
    
    for b_id, b_idx in book_to_idx.items():
        if b_id not in target_liked:
            score = user_predictions[b_idx]
            # Chỉ lấy những sách có điểm dự đoán > 0 (tức là SVD nghĩ user sẽ thích)
            if score > 0.1: 
                recommended_scores[b_id] = score

    # 5. Sắp xếp và lấy Top N
    sorted_recs = sorted(recommended_scores.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    return [{"book_id": b_id, "score": float(score)} for b_id, score in sorted_recs]