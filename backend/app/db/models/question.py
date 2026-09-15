from __future__ import annotations

import enum

from sqlalchemy import Boolean, ForeignKey, Integer, SmallInteger, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class QuestionStage(str, enum.Enum):
    test = "test"
    quiz = "quiz"


class QuestionType(str, enum.Enum):
    single_choice = "single_choice"
    true_false = "true_false"
    fill_blank = "fill_blank"
    matching = "matching"
    ordering = "ordering"


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)
    stage: Mapped[QuestionStage] = mapped_column(SAEnum(QuestionStage, native_enum=False, length=8), nullable=False)
    type: Mapped[QuestionType] = mapped_column(SAEnum(QuestionType, native_enum=False, length=32), nullable=False)
    difficulty: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    # DIQQAT: correct_answer hech qachon student-facing API javoblarida serializatsiya qilinmasin.
    correct_answer: Mapped[dict] = mapped_column(JSONB, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    time_limit_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    answer_options: Mapped[list["AnswerOption"]] = relationship(
        back_populates="question", cascade="all, delete-orphan", order_by="AnswerOption.order"
    )


class AnswerOption(Base):
    __tablename__ = "answer_options"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    # DIQQAT: is_correct hech qachon student-facing API javoblarida serializatsiya qilinmasin.
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    question: Mapped["Question"] = relationship(back_populates="answer_options")
