from pydantic import BaseModel


class SubjectOut(BaseModel):
    id: int
    slug: str
    title: str
    icon: str | None
    color: str | None
    order: int
    progress_pct: float
    is_fallback: bool


class SectionOut(BaseModel):
    id: int
    slug: str
    title: str
    order: int
    is_fallback: bool


class TopicOut(BaseModel):
    id: int
    slug: str
    title: str
    order: int
    status: str  # locked | unlocked | completed
    is_fallback: bool


class StageStatus(BaseModel):
    lesson: str
    test: str
    quiz: str
    homework: str


class LessonOut(BaseModel):
    topic_id: int
    title: str
    content_html: str
    media: dict | None
    is_fallback: bool
    stage_status: StageStatus
