from pathlib import Path
import sys

# Đảm bảo import được module app
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.book_service import load_books
from app.content_based import ContentBasedIndex
from app.ranking_metrics import ranking_metrics

def main():
    # 1. Load Data
    books = load_books()
    index = ContentBasedIndex(books)
    
    # 2. Định nghĩa các bài Test (Người dùng ảo)
    test_cases = [
        {"name": "Fantasy & Magic", "genres": ["fantasy"], "tags": ["magic"]},
        {"name": "Sci-Fi & Space", "genres": ["science-fiction"], "tags": ["space"]},
        {"name": "Mystery & Crime", "genres": ["mystery"], "tags": ["crime"]},
        {"name": "Romance & Love", "genres": ["romance"], "tags": ["love"]},
        {"name": "Horror & Ghost", "genres": ["horror"], "tags": ["ghost"]},
    ]
    
    K = 10 # Đánh giá trên Top 10 sách gợi ý
    
    print(f"{'='*70}")
    print(f"ĐÁNH GIÁ THUẬT TOÁN TF-IDF (CONTENT-BASED) - TOP {K}")
    print(f"{'='*70}")
    print(f"{'Test Case':<20} | {'Relevant':<10} | {'Precision@10':<12} | {'Recall@10':<10} | {'NDCG@10':<10}")
    print("-" * 70)

    total_p, total_r, total_n = 0.0, 0.0, 0.0

    for case in test_cases:
        # Lấy Top K từ thuật toán
        results = index.by_preferences(genres=case["genres"], tags=case["tags"], limit=K)
        recommended_ids = [r.book.id for r in results]
        
        # Tạo tập Ground Truth (Quét toàn bộ data xem ai thực sự khớp)
        wanted_g = set(case["genres"])
        wanted_t = set(case["tags"])
        relevant_ids = set()
        for b in books:
            if (wanted_g & set(b.genres)) or (wanted_t & set(b.tags)):
                relevant_ids.add(b.id)
                
        # Tính điểm
        metrics = ranking_metrics(recommended_ids, relevant_ids, K)
        p_k, r_k, n_k = (metrics[f"{name}@{K}"] for name in ("precision", "recall", "ndcg"))
        
        total_p += p_k
        total_r += r_k
        total_n += n_k

        print(f"{case['name']:<20} | {len(relevant_ids):<10} | {p_k:<12.2f} | {r_k:<10.2f} | {n_k:<10.2f}")

    print("-" * 70)
    num_cases = len(test_cases)
    print(f"{'TRUNG BÌNH CỘNG':<20} | {'':<10} | {total_p/num_cases:<12.2f} | {total_r/num_cases:<10.2f} | {total_n/num_cases:<10.2f}")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
