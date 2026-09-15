from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Lesson, Section, Topic, User
from app.deps import get_current_user, get_db
from app.schemas.content import LessonOut, StageStatus, TopicOut
from app.services.i18n import resolve, resolve_many
from app.services.progress_service import compute_stage_status, compute_topic_status, get_progress_map
from app.services.sanitize import sanitize_html

router = APIRouter(prefix="/api", tags=["topics"])

_SUPPORTED_LANGS = ("uz", "ru", "en")


def _lang_for(current_user: User, lang: str | None) -> str:
    return lang if lang in _SUPPORTED_LANGS else current_user.lang.value


@router.get("/sections/{section_id}/topics", response_model=list[TopicOut])
async def list_topics(
    section_id: int,
    lang: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TopicOut]:
    resolved_lang = _lang_for(current_user, lang)

    section = await db.get(Section, section_id)
    if section is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bo'lim topilmadi")

    topics = (
        await db.execute(select(Topic).where(Topic.section_id == section_id).order_by(Topic.order))
    ).scalars().all()
    topic_ids = [t.id for t in topics]
    titles = await resolve_many(db, "topic", topic_ids, resolved_lang, "title")
    progress_map = await get_progress_map(db, current_user.id, topic_ids)

    result: list[TopicOut] = []
    for index, topic in enumerate(topics):
        # Bosqich-1'da test bosqichi mavjud emas, shuning uchun 2- va keyingi
        # mavzular doim 'locked' bo'lib qoladi (Bosqich-2'da test qo'shilgach o'zgaradi).
        status_value = await compute_topic_status(
            progress_map, topic, is_first_in_section=(index == 0), previous_topic_test_passed=False
        )
        title, is_fallback = titles.get(topic.id, (topic.slug, True))
        result.append(
            TopicOut(
                id=topic.id,
                slug=topic.slug,
                title=title,
                order=topic.order,
                status=status_value,
                is_fallback=is_fallback,
            )
        )
    return result


@router.get("/topics/{topic_id}/lesson", response_model=LessonOut)
async def get_lesson(
    topic_id: int,
    lang: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LessonOut:
    resolved_lang = _lang_for(current_user, lang)

    topic = await db.get(Topic, topic_id)
    if topic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mavzu topilmadi")

    lesson = (await db.execute(select(Lesson).where(Lesson.topic_id == topic_id))).scalar_one_or_none()
    if lesson is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dars kontenti topilmadi")

    title, title_fallback = await resolve(db, "topic", topic_id, resolved_lang, "title", topic.slug)
    content, content_fallback = await resolve(db, "lesson", lesson.id, resolved_lang, "content", lesson.content)

    progress_map = await get_progress_map(db, current_user.id, [topic_id])
    stage_status = compute_stage_status(progress_map, topic_id)

    return LessonOut(
        topic_id=topic_id,
        title=title,
        content_html=sanitize_html(content),
        media=lesson.media,
        is_fallback=title_fallback or content_fallback,
        stage_status=StageStatus(**stage_status),
    )
