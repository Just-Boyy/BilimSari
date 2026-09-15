"""Bosqich-1 uchun namunaviy ma'lumotlarni bazaga yuklaydi.

Ishga tushirish: cd backend && python -m scripts.seed

Idempotent: slug/unique kalitlar bo'yicha upsert qiladi, xavfsiz qayta ishga tushiriladi.
Savol/quiz/uy vazifasi ma'lumotlari ATAYLAB seed qilinmaydi — bu Bosqich-2 ishi.
"""

import asyncio

from sqlalchemy import select

from app.db.models import Lesson, Section, Subject, Topic, Translation
from app.db.session import async_session, engine
from app.db.base import Base
from app.services.sanitize import sanitize_html

LANGS = ("uz", "ru", "en")

SUBJECTS = [
    {
        "slug": "math",
        "icon": "sigma",
        "color": "#5CA904",
        "title": {"uz": "Matematika", "ru": "Математика", "en": "Mathematics"},
    },
    {
        "slug": "english",
        "icon": "languages",
        "color": "#4A8703",
        "title": {"uz": "Ingliz tili", "ru": "Английский язык", "en": "English"},
    },
    {
        "slug": "russian",
        "icon": "book-a",
        "color": "#7DC22B",
        "title": {"uz": "Rus tili", "ru": "Русский язык", "en": "Russian language"},
    },
    {
        "slug": "biology",
        "icon": "leaf",
        "color": "#3FA34D",
        "title": {"uz": "Biologiya", "ru": "Биология", "en": "Biology"},
    },
    {
        "slug": "chemistry",
        "icon": "flask-conical",
        "color": "#6B9E1E",
        "title": {"uz": "Kimyo", "ru": "Химия", "en": "Chemistry"},
    },
    {
        "slug": "native_lang",
        "icon": "book-open",
        "color": "#8FC93D",
        "title": {"uz": "Ona tili", "ru": "Родной язык", "en": "Native language"},
    },
    {
        "slug": "literature",
        "icon": "book-marked",
        "color": "#2F7A1F",
        "title": {"uz": "Adabiyot", "ru": "Литература", "en": "Literature"},
    },
    {
        "slug": "history",
        "icon": "landmark",
        "color": "#5E8C3A",
        "title": {"uz": "Tarix", "ru": "История", "en": "History"},
    },
    {
        "slug": "law",
        "icon": "scale",
        "color": "#4F7942",
        "title": {"uz": "Huquq", "ru": "Право", "en": "Law"},
    },
    {
        "slug": "geography",
        "icon": "globe",
        "color": "#79A82C",
        "title": {"uz": "Geografiya", "ru": "География", "en": "Geography"},
    },
]

SECTION_TITLE = {"uz": "Kirish bo'limi", "ru": "Вводный раздел", "en": "Introduction section"}

TOPIC_TITLE = {
    1: {"uz": "1-mavzu: Asosiy tushunchalar", "ru": "Тема 1: Основные понятия", "en": "Topic 1: Basic concepts"},
    2: {"uz": "2-mavzu: Chuqurlashtirish", "ru": "Тема 2: Углубление", "en": "Topic 2: Going deeper"},
}


def _lesson_html(subject_title: str, topic_no: int, lang: str, is_math: bool) -> str:
    intro = {
        "uz": f"<h2>{subject_title} — {topic_no}-mavzu</h2><p>Bu namunaviy dars matni. Haqiqiy kontent admin panel orqali to'ldiriladi.</p>",
        "ru": f"<h2>{subject_title} — Тема {topic_no}</h2><p>Это пример текста урока. Реальный контент будет добавлен через админ-панель.</p>",
        "en": f"<h2>{subject_title} — Topic {topic_no}</h2><p>This is sample lesson text. Real content will be added via the admin panel.</p>",
    }[lang]

    if is_math and topic_no == 1:
        extra = {
            "uz": (
                "<p>Formulaga misol: $$a^2 + b^2 = c^2$$</p>"
                "<table><tr><th>Tomon</th><th>Uzunlik</th></tr>"
                "<tr><td>a</td><td>3</td></tr><tr><td>b</td><td>4</td></tr><tr><td>c</td><td>5</td></tr></table>"
            ),
            "ru": (
                "<p>Пример формулы: $$a^2 + b^2 = c^2$$</p>"
                "<table><tr><th>Сторона</th><th>Длина</th></tr>"
                "<tr><td>a</td><td>3</td></tr><tr><td>b</td><td>4</td></tr><tr><td>c</td><td>5</td></tr></table>"
            ),
            "en": (
                "<p>Formula example: $$a^2 + b^2 = c^2$$</p>"
                "<table><tr><th>Side</th><th>Length</th></tr>"
                "<tr><td>a</td><td>3</td></tr><tr><td>b</td><td>4</td></tr><tr><td>c</td><td>5</td></tr></table>"
            ),
        }[lang]
        return sanitize_html(intro + extra)

    return sanitize_html(intro)

    return intro


async def seed() -> None:
    # Jadvallar hali yaratilmagan bo'lsa (Alembic ishga tushirilmagan holatda ham
    # skript tez sinov qilinishi uchun) - metadata orqali yaratib qo'yamiz.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        for order, subj in enumerate(SUBJECTS):
            subject = (await db.execute(select(Subject).where(Subject.slug == subj["slug"]))).scalar_one_or_none()
            if subject is None:
                subject = Subject(slug=subj["slug"], icon=subj["icon"], color=subj["color"], order=order)
                db.add(subject)
                await db.flush()

            for lang in LANGS:
                await _upsert_translation(db, "subject", subject.id, lang, "title", subj["title"][lang])

            section = (
                await db.execute(select(Section).where(Section.subject_id == subject.id, Section.slug == "intro"))
            ).scalar_one_or_none()
            if section is None:
                section = Section(subject_id=subject.id, slug="intro", order=0)
                db.add(section)
                await db.flush()

            for lang in LANGS:
                await _upsert_translation(db, "section", section.id, lang, "title", SECTION_TITLE[lang])

            is_math = subj["slug"] == "math"
            for topic_no in (1, 2):
                topic_slug = f"topic-{topic_no}"
                topic = (
                    await db.execute(
                        select(Topic).where(Topic.section_id == section.id, Topic.slug == topic_slug)
                    )
                ).scalar_one_or_none()
                if topic is None:
                    topic = Topic(section_id=section.id, slug=topic_slug, order=topic_no - 1)
                    db.add(topic)
                    await db.flush()

                for lang in LANGS:
                    await _upsert_translation(db, "topic", topic.id, lang, "title", TOPIC_TITLE[topic_no][lang])

                lesson = (await db.execute(select(Lesson).where(Lesson.topic_id == topic.id))).scalar_one_or_none()
                base_content = _lesson_html(subj["title"]["uz"], topic_no, "uz", is_math)
                if lesson is None:
                    lesson = Lesson(topic_id=topic.id, content=base_content, media=None)
                    db.add(lesson)
                    await db.flush()
                else:
                    lesson.content = base_content

                for lang in ("ru", "en"):
                    content = _lesson_html(subj["title"][lang], topic_no, lang, is_math)
                    await _upsert_translation(db, "lesson", lesson.id, lang, "content", content)

        await db.commit()

    print(f"[seed] {len(SUBJECTS)} ta fan, har biriga 1 bo'lim va 2 mavzu (uz/ru/en) yuklandi.")
    print("[seed] Question/quiz/homework seeding Bosqich-2ga qoldirildi.")


async def _upsert_translation(db, entity_type: str, entity_id: int, lang: str, field: str, value: str) -> None:
    existing = (
        await db.execute(
            select(Translation).where(
                Translation.entity_type == entity_type,
                Translation.entity_id == entity_id,
                Translation.lang == lang,
                Translation.field == field,
            )
        )
    ).scalar_one_or_none()
    if existing is None:
        db.add(Translation(entity_type=entity_type, entity_id=entity_id, lang=lang, field=field, value=value))
    else:
        existing.value = value


if __name__ == "__main__":
    asyncio.run(seed())
