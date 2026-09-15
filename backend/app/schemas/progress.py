from pydantic import BaseModel


class ProgressCompleteRequest(BaseModel):
    topic_id: int
    stage: str  # Bosqich-1: faqat "lesson" qabul qilinadi


class NextUnlocked(BaseModel):
    stage: str | None
    topic_id: int | None


class ProgressCompleteResponse(BaseModel):
    topic_id: int
    stage: str
    is_completed: bool
    next_unlocked: NextUnlocked | None
