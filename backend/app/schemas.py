from pydantic import BaseModel, Field


class Book(BaseModel):
    id: str
    title: str
    author: str
    genres: list[str]
    tags: list[str]
    description: str
    language: str
    pages: int | None = Field(default=None, gt=0)