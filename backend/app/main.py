from fastapi import FastAPI

from app.book_service import load_books
from app.schemas import Book


app = FastAPI(title="Book Recommendation API")


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/books", response_model=list[Book])
def get_books():
    return load_books()