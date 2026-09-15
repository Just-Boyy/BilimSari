"""Mavzu/bosqich ochilish (lock/unlock) mantig'i.

Bosqich-1'da faqat 'lesson' bosqichi ishlaydi. Test hali mavjud emasligi
sababli, har bo'limning FAQAT birinchi mavzusi ochiq bo'ladi — bu kutilgan
holat va Bosqich-2'da test qo'shilgach o'zgaradi.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Progress, ProgressStage, Topic


async def get_progress_map(
    db: AsyncSession, user_id: int, topic_ids: list[int]
) -> dict[tuple[int, str], Progress]:
    if not topic_ids:
        return {}
    rows = (
        await db.execute(select(Progress).where(Progress.user_id == user_id, Progress.topic_id.in_(topic_ids)))
    ).scalars().all()
    return {(row.topic_id, row.stage.value): row for row in rows}


async def compute_topic_status(
    progress_map: dict[tuple[int, str], Progress],
    topic: Topic,
    is_first_in_section: bool,
    previous_topic_test_passed: bool,
) -> str:
    lesson_progress = progress_map.get((topic.id, ProgressStage.lesson.value))
    if lesson_progress and lesson_progress.is_completed:
        return "completed"

    if is_first_in_section or previous_topic_test_passed:
        return "unlocked"

    return "locked"


def compute_stage_status(progress_map: dict[tuple[int, str], Progress], topic_id: int) -> dict[str, str]:
    lesson = progress_map.get((topic_id, ProgressStage.lesson.value))
    lesson_done = bool(lesson and lesson.is_completed)

    return {
        "lesson": "completed" if lesson_done else "unlocked",
        "test": "unlocked" if lesson_done else "locked",
        "quiz": "locked",
        "homework": "locked",
    }
