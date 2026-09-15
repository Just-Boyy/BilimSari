from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Progress, ProgressStage, Section, Subject, Topic, User
from app.deps import get_current_user, get_db
from app.schemas.content import SectionOut, SubjectOut
from app.services.i18n import resolve_many

router = APIRouter(prefix="/api", tags=["subjects"])

_SUPPORTED_LANGS = ("uz", "ru", "en")


def _lang_for(current_user: User, lang: str | None) -> str:
    return lang if lang in _SUPPORTED_LANGS else current_user.lang.value


@router.get("/subjects", response_model=list[SubjectOut])
async def list_subjects(
    lang: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SubjectOut]:
    resolved_lang = _lang_for(current_user, lang)

    subjects = (await db.execute(select(Subject).order_by(Subject.order))).scalars().all()
    subject_ids = [s.id for s in subjects]
    titles = await resolve_many(db, "subject", subject_ids, resolved_lang, "title")

    topic_rows = (
        await db.execute(
            select(Topic.id, Section.subject_id)
            .join(Section, Topic.section_id == Section.id)
            .where(Section.subject_id.in_(subject_ids))
        )
    ).all()

    topics_by_subject: dict[int, list[int]] = {}
    for topic_id, subject_id in topic_rows:
        topics_by_subject.setdefault(subject_id, []).append(topic_id)

    all_topic_ids = [row[0] for row in topic_rows]
    completed_topic_ids: set[int] = set()
    if all_topic_ids:
        completed_topic_ids = set(
            (
                await db.execute(
                    select(Progress.topic_id).where(
                        Progress.user_id == current_user.id,
                        Progress.topic_id.in_(all_topic_ids),
                        Progress.stage == ProgressStage.lesson,
                        Progress.is_completed.is_(True),
                    )
                )
            )
            .scalars()
            .all()
        )

    result: list[SubjectOut] = []
    for subject in subjects:
        topic_ids = topics_by_subject.get(subject.id, [])
        pct = (
            round(100 * len([t for t in topic_ids if t in completed_topic_ids]) / len(topic_ids), 1)
            if topic_ids
            else 0.0
        )
        title, is_fallback = titles.get(subject.id, (subject.slug, True))
        result.append(
            SubjectOut(
                id=subject.id,
                slug=subject.slug,
                title=title,
                icon=subject.icon,
                color=subject.color,
                order=subject.order,
                progress_pct=pct,
                is_fallback=is_fallback,
            )
        )
    return result


@router.get("/subjects/{subject_id}/sections", response_model=list[SectionOut])
async def list_sections(
    subject_id: int,
    lang: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SectionOut]:
    resolved_lang = _lang_for(current_user, lang)

    subject = await db.get(Subject, subject_id)
    if subject is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fan topilmadi")

    sections = (
        await db.execute(select(Section).where(Section.subject_id == subject_id).order_by(Section.order))
    ).scalars().all()
    section_ids = [s.id for s in sections]
    titles = await resolve_many(db, "section", section_ids, resolved_lang, "title")

    return [
        SectionOut(
            id=section.id,
            slug=section.slug,
            title=titles.get(section.id, (section.slug, True))[0],
            order=section.order,
            is_fallback=titles.get(section.id, (section.slug, True))[1],
        )
        for section in sections
    ]
