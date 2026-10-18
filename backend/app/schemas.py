from pydantic import BaseModel, Field, field_validator, model_validator


class Book(BaseModel):
    id: str
    title: str
    author: str
    genres: list[str]
    tags: list[str]
    description: str
    language: str
    pages: int | None = Field(default=None, gt=0)


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


class RecommendationResult(BaseModel):
    book: Book
    score: float = Field(ge=0, le=1)
    reasons: list[str]