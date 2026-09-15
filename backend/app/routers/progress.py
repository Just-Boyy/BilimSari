from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Progress, ProgressStage, Topic, User
from app.deps import get_current_user, get_db
from app.schemas.progress import NextUnlocked, ProgressCompleteRequest, ProgressCompleteResponse

router = APIRouter(prefix="/api/progress", tags=["progress"])


@router.post("/complete", response_model=ProgressCompleteResponse)
async def complete_stage(
    payload: ProgressCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProgressCompleteResponse:
    if payload.stage != "lesson":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bosqich-1'da faqat 'lesson' bosqichini yakunlash mumkin",
        )

    topic = await db.get(Topic, payload.topic_id)
    if topic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mavzu topilmadi")

    progress = (
        await db.execute(
            select(Progress).where(
                Progress.user_id == current_user.id,
                Progress.topic_id == payload.topic_id,
                Progress.stage == ProgressStage.lesson,
            )
        )
    ).scalar_one_or_none()

    now = datetime.now(timezone.utc)
    if progress is None:
        progress = Progress(
            user_id=current_user.id,
            topic_id=payload.topic_id,
            stage=ProgressStage.lesson,
            is_completed=True,
            completed_at=now,
        )
        db.add(progress)
    else:
        progress.is_completed = True
        progress.completed_at = now

    await db.commit()

    return ProgressCompleteResponse(
        topic_id=payload.topic_id,
        stage="lesson",
        is_completed=True,
        next_unlocked=NextUnlocked(stage="test", topic_id=payload.topic_id),
    )
