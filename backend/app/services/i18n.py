"""Kontent tarjimalarini `translations` jadvalidan o'qish, topilmasa 'uz'ga qaytish."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Translation

FALLBACK_LANG = "uz"


async def resolve(
    db: AsyncSession,
    entity_type: str,
    entity_id: int,
    lang: str,
    field: str,
    fallback_value: str | None = None,
) -> tuple[str, bool]:
    """Bitta (entity, field) uchun berilgan tildagi tarjimani qaytaradi.

    Qaytadi: (qiymat, is_fallback). is_fallback=True bo'lsa, frontend
    "bu tilda hali mavjud emas" belgisini chiqarishi kerak.
    """
    row = await db.scalar(
        select(Translation).where(
            Translation.entity_type == entity_type,
            Translation.entity_id == entity_id,
            Translation.lang == lang,
            Translation.field == field,
        )
    )
    if row:
        return row.value, False

    if lang != FALLBACK_LANG:
        uz_row = await db.scalar(
            select(Translation).where(
                Translation.entity_type == entity_type,
                Translation.entity_id == entity_id,
                Translation.lang == FALLBACK_LANG,
                Translation.field == field,
            )
        )
        if uz_row:
            return uz_row.value, True

    return fallback_value or "", True


async def resolve_many(
    db: AsyncSession,
    entity_type: str,
    entity_ids: list[int],
    lang: str,
    field: str,
) -> dict[int, tuple[str, bool]]:
    """Bir nechta entity uchun bitta so'rov bilan tarjima qidiradi (N+1 muammosining oldini oladi)."""
    if not entity_ids:
        return {}

    rows = (
        await db.execute(
            select(Translation).where(
                Translation.entity_type == entity_type,
                Translation.entity_id.in_(entity_ids),
                Translation.field == field,
                Translation.lang.in_({lang, FALLBACK_LANG}),
            )
        )
    ).scalars().all()

    by_id: dict[int, dict[str, str]] = {}
    for row in rows:
        by_id.setdefault(row.entity_id, {})[row.lang] = row.value

    result: dict[int, tuple[str, bool]] = {}
    for entity_id in entity_ids:
        langs = by_id.get(entity_id, {})
        if lang in langs:
            result[entity_id] = (langs[lang], False)
        elif FALLBACK_LANG in langs:
            result[entity_id] = (langs[FALLBACK_LANG], True)
        else:
            result[entity_id] = ("", True)
    return result
