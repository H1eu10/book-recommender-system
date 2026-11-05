from typing import Literal
from pydantic import BaseModel, Field, field_validator, model_validator

class BookTranslation(BaseModel):
    title: str
    description: str

class Book(BaseModel):
    id: str
    title: str
    author: str
    genres: list[str]
    tags: list[str]
    description: str
    language: str
    pages: int | None = Field(default=None, gt=0)

    work_id: str | None = None
    original_language: str | None = None
    isbn: str | None = None
    source_url: str | None = None

    translations: dict[str, BookTranslation] = Field(
        default_factory=dict
    )

    metadata_notes: dict[str, str] = Field(
        default_factory=dict
    )

class RecommendationRequest(BaseModel):
    genres: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    language: str | None = None
    max_pages: int | None = Field(default=None, gt=0)
    limit: int = Field(default=5, ge=1, le=20)

    @field_validator("genres", "tags")
    @classmethod
    def normalize_preferences(cls, values: list[str]) -> list[str]:
        return sorted({
            value.strip().lower()
            for value in values
            if value.strip()
        })

    @field_validator("language")
    @classmethod
    def normalize_language(cls, value: str | None) -> str | None:
        if value is None:
            return None

        return value.strip().lower() or None

    @model_validator(mode="after")
    def require_preferences(self):
        if not self.genres and not self.tags:
            raise ValueError("Select at least one genre or topic.")

        return self


class RecommendationExplanation(BaseModel):
    code: Literal["genres", "themes", "shared_genres", "shared_themes", "text_similarity", "history", "popularity"]
    values: list[str] = Field(default_factory=list)


class RecommendationResult(BaseModel):
    book: Book
    score: float = Field(ge=0, le=1)
    reasons: list[str]
    explanations: list[RecommendationExplanation] = Field(default_factory=list)

class SimilarRequest(BaseModel):
    book_id: str
    limit: int = Field(default=10, ge=1, le=30)


class PersonalizedRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    model: Literal["popularity", "itemcf", "ncf", "lightgcn"] = "lightgcn"
    limit: int = Field(default=5, ge=1, le=20)

    @field_validator("user_id")
    @classmethod
    def normalize_user_id(cls, value):
        if not value.strip():
            raise ValueError("User ID cannot be blank")
        return value.strip()


class PersonalizedResult(BaseModel):
    book: Book
    score: float = Field(allow_inf_nan=False)
    explanations: list[RecommendationExplanation]


class PersonalizedResponse(BaseModel):
    model: str
    score_type: Literal["ranking"] = "ranking"
    fallback: bool
    results: list[PersonalizedResult]
