"""Immutable skill version model."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.persistence.models.base import Base

if TYPE_CHECKING:
    from app.persistence.models.skill import Skill
    from app.persistence.models.skill_version_checksum import SkillVersionChecksum


class SkillVersion(Base):
    """Represents immutable `skill@version` metadata."""

    __tablename__ = "skill_versions"
    __table_args__ = (
        UniqueConstraint("skill_fk", "version", name="uq_skill_versions_skill_fk_version"),
        Index(
            "ix_skill_versions_skill_fk_published_at_id",
            "skill_fk",
            "published_at",
            "id",
        ),
        Index("ix_skill_versions_skill_fk_version", "skill_fk", "version"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    skill_fk: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[str] = mapped_column(Text, nullable=False)
    manifest_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    artifact_rel_path: Mapped[str] = mapped_column(Text, nullable=False)
    artifact_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    skill: Mapped[Skill] = relationship(back_populates="versions")
    checksum: Mapped[SkillVersionChecksum] = relationship(
        back_populates="skill_version",
        uselist=False,
        cascade="all, delete-orphan",
    )
