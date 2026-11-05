import json
import random
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BOOKS_FILE = PROJECT_ROOT / "data" / "books.sample.json"
USERS_FILE = PROJECT_ROOT / "data" / "user_interactions.json"

def main():
    books = json.loads(BOOKS_FILE.read_text(encoding="utf-8"))
    
    book_weights = {b["id"]: random.randint(1, 100) for b in books}
    all_book_ids = list(book_weights.keys())
    
    categories = {
        "fantasy": [b["id"] for b in books if "fantasy" in b["genres"]],
        "sci-fi": [b["id"] for b in books if "science-fiction" in b["genres"]],
        "mystery": [b["id"] for b in books if "mystery" in b["genres"]],
        "romance": [b["id"] for b in books if "romance" in b["genres"]],
        "horror": [b["id"] for b in books if "horror" in b["genres"]],
    }
    
    users = {}
    for i in range(1, 1001):
        user_id = f"user_{i:03d}"
        
        user_type = random.choices(
            ["casual", "regular", "power_user"], 
            weights=[0.3, 0.5, 0.2], 
            k=1
        )[0]
        
        if user_type == "casual":
            num_likes = random.randint(3, 6)
            core_genres = random.sample(list(categories.keys()), k=1)
        elif user_type == "regular":
            num_likes = random.randint(8, 15)
            core_genres = random.sample(list(categories.keys()), k=random.choice([1, 2]))
        else: # power_user
            num_likes = random.randint(20, 35)
            core_genres = random.sample(list(categories.keys()), k=random.choice([2, 3]))
            
        liked_books = set()
        
        candidate_books = []
        for genre in core_genres:
            candidate_books.extend(categories[genre])
        candidate_books = list(set(candidate_books))
        
        candidate_weights = [book_weights[b_id] for b_id in candidate_books]
        
        actual_likes = min(num_likes, len(candidate_books))
        
        if actual_likes > 0:
            chosen_books = random.choices(candidate_books, weights=candidate_weights, k=actual_likes)
            liked_books.update(chosen_books)
            
        noise_count = random.randint(0, 2)
        if noise_count > 0:
            noise = random.sample(all_book_ids, k=noise_count)
            liked_books.update(noise)

        users[user_id] = list(liked_books)

    USERS_FILE.write_text(json.dumps(users, indent=2), encoding="utf-8")
    print(f"✅ Đã tạo xong 1000 người dùng thực tế tại {USERS_FILE}")
    
    total_interactions = sum(len(b) for b in users.values())
    print(f"📊 Tổng số lượt Like: {total_interactions}")
    print(f"📊 Trung bình mỗi user like: {total_interactions / len(users):.1f} cuốn")

if __name__ == "__main__":
    main()