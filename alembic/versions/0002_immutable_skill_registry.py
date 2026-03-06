"""Create immutable skill registry tables.

Revision ID: 0002_immutable_skill_registry
Revises: 0001_baseline_audit_event
Create Date: 2026-03-06
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "0002_immutable_skill_registry"
down_revision = "0001_baseline_audit_event"
branch_labels = None
depends_on = None


SEMVER_PATTERN = (
    r"^(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)\."
    r"(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)


def upgrade() -> None:
    op.create_table(
        "skills",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("skill_id", sa.Text(), nullable=False, unique=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )

    op.create_table(
        "skill_versions",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "skill_fk",
            sa.BigInteger(),
            sa.ForeignKey("skills.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("version", sa.Text(), nullable=False),
        sa.Column("manifest_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("artifact_rel_path", sa.Text(), nullable=False),
        sa.Column("artifact_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column(
            "published_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint("skill_fk", "version", name="uq_skill_versions_skill_fk_version"),
        sa.CheckConstraint(
            f"version ~ '{SEMVER_PATTERN}'", name="ck_skill_versions_version_semver"
        ),
    )

    op.create_index(
        "ix_skill_versions_skill_fk_published_at_id",
        "skill_versions",
        ["skill_fk", "published_at", "id"],
    )
    op.create_index(
        "ix_skill_versions_skill_fk_version",
        "skill_versions",
        ["skill_fk", "version"],
    )

    op.create_table(
        "skill_version_checksums",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "skill_version_fk",
            sa.BigInteger(),
            sa.ForeignKey("skill_versions.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("algorithm", sa.String(length=20), nullable=False),
        sa.Column("digest", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "algorithm = 'sha256'",
            name="ck_skill_version_checksums_algorithm",
        ),
        sa.CheckConstraint(
            "char_length(digest) = 64", name="ck_skill_version_checksums_digest_length"
        ),
    )


def downgrade() -> None:
    op.drop_table("skill_version_checksums")
    op.drop_index("ix_skill_versions_skill_fk_version", table_name="skill_versions")
    op.drop_index("ix_skill_versions_skill_fk_published_at_id", table_name="skill_versions")
    op.drop_table("skill_versions")
    op.drop_table("skills")
