"""Checksum model for immutable skill versions."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.persistence.models.base import Base

if TYPE_CHECKING:
    from app.persistence.models.skill_version import SkillVersion


class SkillVersionChecksum(Base):
    """Represents checksum metadata for one immutable skill version."""

    __tablename__ = "skill_version_checksums"
    __table_args__ = (
        CheckConstraint(
            "algorithm = 'sha256'",
            name="ck_skill_version_checksums_algorithm",
        ),
        CheckConstraint(
            "char_length(digest) = 64", name="ck_skill_version_checksums_digest_length"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    skill_version_fk: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("skill_versions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    algorithm: Mapped[str] = mapped_column(String(20), nullable=False)
    digest: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    skill_version: Mapped[SkillVersion] = relationship(back_populates="checksum")
