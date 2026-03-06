"""Immutable skill root model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.persistence.models.base import Base

if TYPE_CHECKING:
    from app.persistence.models.skill_version import SkillVersion


class Skill(Base):
    """Represents a logical skill identifier."""

    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    skill_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    versions: Mapped[list[SkillVersion]] = relationship(
        back_populates="skill",
        cascade="all, delete-orphan",
    )
