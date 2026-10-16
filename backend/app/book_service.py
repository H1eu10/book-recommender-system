import json
from pathlib import Path

from app.schemas import Book


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BOOKS_FILE = PROJECT_ROOT / "data" / "books.sample.json"


def load_books() -> list[Book]:
    with BOOKS_FILE.open(encoding="utf-8") as file:
        data = json.load(file)

    return [Book.model_validate(item) for item in data]