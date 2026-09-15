from pydantic import BaseModel, field_validator


class UserUpdateRequest(BaseModel):
    lang: str | None = None
    grade: int | None = None

    @field_validator("lang")
    @classmethod
    def validate_lang(cls, value: str | None) -> str | None:
        if value is not None and value not in ("uz", "ru", "en"):
            raise ValueError("lang faqat 'uz', 'ru' yoki 'en' bo'lishi mumkin")
        return value
