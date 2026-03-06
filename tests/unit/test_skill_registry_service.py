"""Unit tests for immutable skill registry core behavior."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.core.ports import ArtifactWriteResult, StoredSkillVersion
from app.core.skill_registry import (
    DuplicateSkillVersionError,
    IntegrityCheckFailedError,
    SkillManifestData,
    SkillRegistryService,
    SkillVersionNotFoundError,
)


class FakeRegistry:
    """In-memory stub for core registry tests."""

    def __init__(self) -> None:
        self._records: dict[tuple[str, str], StoredSkillVersion] = {}

    def version_exists(self, skill_id: str, version: str) -> bool:
        return (skill_id, version) in self._records

    def create_version(
        self,
        *,
        manifest_json: dict[str, object],
        artifact_relative_path: str,
        artifact_size_bytes: int,
        checksum: object,
    ) -> StoredSkillVersion:
        skill_id = str(manifest_json["skill_id"])
        version = str(manifest_json["version"])
        key = (skill_id, version)
        if key in self._records:
            raise DuplicateSkillVersionError(skill_id=skill_id, version=version)

        checksum_algorithm = str(checksum.algorithm)
        checksum_digest = str(checksum.digest)
        record = StoredSkillVersion(
            skill_id=skill_id,
            version=version,
            manifest_json=manifest_json,
            artifact_relative_path=artifact_relative_path,
            artifact_size_bytes=artifact_size_bytes,
            checksum_algorithm=checksum_algorithm,
            checksum_digest=checksum_digest,
            published_at=datetime.now(tz=UTC),
        )
        self._records[key] = record
        return record

    def get_version(self, skill_id: str, version: str) -> StoredSkillVersion | None:
        return self._records.get((skill_id, version))

    def list_versions(self, skill_id: str) -> tuple[StoredSkillVersion, ...]:
        return tuple(
            record
            for (stored_skill_id, _), record in self._records.items()
            if stored_skill_id == skill_id
        )


class FakeArtifactStore:
    """In-memory artifact store stub."""

    def __init__(self) -> None:
        self.artifacts: dict[str, bytes] = {}

    def store_immutable_artifact(
        self,
        *,
        skill_id: str,
        version: str,
        artifact_bytes: bytes,
        manifest_json: dict[str, object],
    ) -> ArtifactWriteResult:
        relative_path = f"skills/{skill_id}/{version}/artifact.bin"
        self.artifacts[relative_path] = artifact_bytes
        return ArtifactWriteResult(relative_path=relative_path, size_bytes=len(artifact_bytes))

    def read_artifact(self, relative_path: str) -> bytes:
        return self.artifacts[relative_path]


class FakeAuditRecorder:
    """Audit stub collecting event names."""

    def __init__(self) -> None:
        self.events: list[str] = []

    def record_event(self, *, event_type: str, payload: dict[str, object] | None = None) -> None:
        self.events.append(event_type)


def _manifest(skill_id: str, version: str) -> SkillManifestData:
    return SkillManifestData(
        schema_version="1.0",
        skill_id=skill_id,
        version=version,
        name="Python Lint",
        description="Linting skill",
        tags=("python", "lint"),
        depends_on=(),
        extends=(),
        conflicts_with=(),
        overlaps_with=(),
    )


@pytest.mark.unit
def test_publish_version_returns_checksum_and_records_audit() -> None:
    registry = FakeRegistry()
    artifact_store = FakeArtifactStore()
    audit_recorder = FakeAuditRecorder()
    service = SkillRegistryService(
        registry=registry,
        artifact_store=artifact_store,
        audit_recorder=audit_recorder,
    )

    response = service.publish_version(
        manifest=_manifest(skill_id="python.lint", version="1.0.0"),
        artifact_bytes=b"hello world",
    )

    assert response.skill_id == "python.lint"
    assert response.version == "1.0.0"
    assert response.artifact.relative_path == "skills/python.lint/1.0.0/artifact.bin"
    assert response.checksum.algorithm == "sha256"
    assert (
        response.checksum.digest
        == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    )
    assert "skill.version_published" in audit_recorder.events


@pytest.mark.unit
def test_publish_version_rejects_duplicates() -> None:
    registry = FakeRegistry()
    artifact_store = FakeArtifactStore()
    audit_recorder = FakeAuditRecorder()
    service = SkillRegistryService(
        registry=registry,
        artifact_store=artifact_store,
        audit_recorder=audit_recorder,
    )
    manifest = _manifest(skill_id="python.lint", version="1.0.0")
    service.publish_version(manifest=manifest, artifact_bytes=b"v1")

    with pytest.raises(DuplicateSkillVersionError):
        service.publish_version(manifest=manifest, artifact_bytes=b"v1")


@pytest.mark.unit
def test_get_version_raises_not_found_for_unknown_skill() -> None:
    service = SkillRegistryService(
        registry=FakeRegistry(),
        artifact_store=FakeArtifactStore(),
        audit_recorder=FakeAuditRecorder(),
    )

    with pytest.raises(SkillVersionNotFoundError):
        service.get_version(skill_id="missing.skill", version="1.0.0")


@pytest.mark.unit
def test_get_version_detects_checksum_mismatch() -> None:
    registry = FakeRegistry()
    artifact_store = FakeArtifactStore()
    audit_recorder = FakeAuditRecorder()
    service = SkillRegistryService(
        registry=registry,
        artifact_store=artifact_store,
        audit_recorder=audit_recorder,
    )

    published = service.publish_version(
        manifest=_manifest(skill_id="python.lint", version="1.0.0"),
        artifact_bytes=b"trusted payload",
    )
    artifact_store.artifacts[published.artifact.relative_path] = b"tampered payload"

    with pytest.raises(IntegrityCheckFailedError):
        service.get_version(skill_id="python.lint", version="1.0.0")
