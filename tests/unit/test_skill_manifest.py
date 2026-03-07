"""Unit tests for skill manifest validation rules."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.interface.api.skills import SkillManifest


@pytest.mark.unit
def test_skill_manifest_accepts_forward_compatible_relationship_fields() -> None:
    manifest = SkillManifest.model_validate(
        {
            "schema_version": "1.0",
            "skill_id": "python.lint",
            "version": "1.2.3",
            "name": "Python Lint",
            "description": "Linting skill",
            "tags": ["python", "lint"],
            "depends_on": [{"skill_id": "core.base", "version": "1.0.0"}],
            "extends": [{"skill_id": "python.base", "version": "2.0.0"}],
            "conflicts_with": [{"skill_id": "ruby.lint", "version": "1.0.0"}],
            "overlaps_with": [{"skill_id": "python.format", "version": "1.0.0"}],
        },
    )

    assert manifest.skill_id == "python.lint"
    assert manifest.version == "1.2.3"
    assert manifest.depends_on is not None
    assert manifest.depends_on[0].version == "1.0.0"


@pytest.mark.unit
def test_skill_manifest_rejects_non_semver_version() -> None:
    with pytest.raises(ValidationError):
        SkillManifest.model_validate(
            {
                "schema_version": "1.0",
                "skill_id": "python.lint",
                "version": "v1",
                "name": "Python Lint",
            },
        )


@pytest.mark.unit
def test_skill_manifest_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        SkillManifest.model_validate(
            {
                "schema_version": "1.0",
                "skill_id": "python.lint",
                "version": "1.0.0",
                "name": "Python Lint",
                "extra_field": "not allowed",
            },
        )
