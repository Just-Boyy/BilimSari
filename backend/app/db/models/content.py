from __future__ import annotations

from sqlalchemy import ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    icon: Mapped[str | None] = mapped_column(String(64), nullable=True)
    color: Mapped[str | None] = mapped_column(String(16), nullable=True)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    sections: Mapped[list["Section"]] = relationship(
        back_populates="subject", cascade="all, delete-orphan", order_by="Section.order"
    )


class Section(Base):
    __tablename__ = "sections"

    id: Mapped[int] = mapped_column(primary_key=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    subject: Mapped["Subject"] = relationship(back_populates="sections")
    topics: Mapped[list["Topic"]] = relationship(
        back_populates="section", cascade="all, delete-orphan", order_by="Topic.order"
    )

    __table_args__ = (UniqueConstraint("subject_id", "slug", name="uq_section_subject_slug"),)


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    section_id: Mapped[int] = mapped_column(ForeignKey("sections.id", ondelete="CASCADE"), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(64), nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pass_threshold: Mapped[int] = mapped_column(Integer, default=60, nullable=False)

    section: Mapped["Section"] = relationship(back_populates="topics")
    lesson: Mapped["Lesson"] = relationship(back_populates="topic", cascade="all, delete-orphan", uselist=False)

    __table_args__ = (
        UniqueConstraint("section_id", "slug", name="uq_topic_section_slug"),
        Index("ix_topic_section_order", "section_id", "order"),
    )
