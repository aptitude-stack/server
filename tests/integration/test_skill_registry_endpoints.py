"""Integration tests for immutable skill registry endpoints."""

from __future__ import annotations

import base64
import json
from pathlib import Path
from uuid import uuid4

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient

from alembic import command
from app.main import create_app


@pytest.fixture
def migrated_registry_database(require_integration_database: str) -> str:
    config = Config("alembic.ini")
    config.set_main_option("script_location", "alembic")
    config.set_main_option("sqlalchemy.url", require_integration_database)
    command.upgrade(config, "head")
    return require_integration_database


def _manifest(skill_id: str, version: str) -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "skill_id": skill_id,
        "version": version,
        "name": "Python Lint",
        "description": "Linting skill",
        "tags": ["python", "lint"],
        "depends_on": [],
        "extends": [],
        "conflicts_with": [],
        "overlaps_with": [],
    }


def _publish(
    *,
    client: TestClient,
    skill_id: str,
    version: str,
    artifact_bytes: bytes,
) -> dict[str, object]:
    response = client.post(
        "/skills/publish",
        data={"manifest": json.dumps(_manifest(skill_id=skill_id, version=version))},
        files={"artifact": ("artifact.bin", artifact_bytes, "application/octet-stream")},
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.integration
def test_publish_fetch_and_list_skill_versions(
    monkeypatch: pytest.MonkeyPatch,
    migrated_registry_database: str,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("DATABASE_URL", migrated_registry_database)
    monkeypatch.setenv("ARTIFACT_ROOT_DIR", str(tmp_path / "artifacts"))
    skill_id = f"python.lint.{uuid4().hex}"

    with TestClient(create_app()) as client:
        _publish(client=client, skill_id=skill_id, version="1.0.0", artifact_bytes=b"v1")
        _publish(client=client, skill_id=skill_id, version="1.1.0", artifact_bytes=b"v11")
        _publish(client=client, skill_id=skill_id, version="2.0.0", artifact_bytes=b"v2")

        for expected in ["1.0.0", "1.1.0", "2.0.0"]:
            response = client.get(f"/skills/{skill_id}/{expected}")
            assert response.status_code == 200
            body = response.json()
            assert body["skill_id"] == skill_id
            assert body["version"] == expected
            assert body["checksum"]["algorithm"] == "sha256"
            assert base64.b64decode(body["artifact_base64"]) in {b"v1", b"v11", b"v2"}

        list_first = client.get(f"/skills/{skill_id}")
        list_second = client.get(f"/skills/{skill_id}")

    assert list_first.status_code == 200
    assert list_second.status_code == 200
    assert list_first.json() == list_second.json()
    assert [item["version"] for item in list_first.json()["versions"]] == [
        "2.0.0",
        "1.1.0",
        "1.0.0",
    ]


@pytest.mark.integration
def test_duplicate_publish_returns_409(
    monkeypatch: pytest.MonkeyPatch,
    migrated_registry_database: str,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("DATABASE_URL", migrated_registry_database)
    monkeypatch.setenv("ARTIFACT_ROOT_DIR", str(tmp_path / "artifacts"))
    skill_id = f"python.lint.{uuid4().hex}"

    with TestClient(create_app()) as client:
        _publish(
            client=client,
            skill_id=skill_id,
            version="1.0.0",
            artifact_bytes=b"v1",
        )
        duplicate = client.post(
            "/skills/publish",
            data={"manifest": json.dumps(_manifest(skill_id=skill_id, version="1.0.0"))},
            files={"artifact": ("artifact.bin", b"v1", "application/octet-stream")},
        )

    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "DUPLICATE_SKILL_VERSION"


@pytest.mark.integration
def test_fetch_detects_corrupted_artifact_checksum(
    monkeypatch: pytest.MonkeyPatch,
    migrated_registry_database: str,
    tmp_path: Path,
) -> None:
    artifact_root = tmp_path / "artifacts"
    monkeypatch.setenv("DATABASE_URL", migrated_registry_database)
    monkeypatch.setenv("ARTIFACT_ROOT_DIR", str(artifact_root))
    skill_id = f"python.lint.{uuid4().hex}"

    with TestClient(create_app()) as client:
        publish = _publish(
            client=client, skill_id=skill_id, version="1.0.0", artifact_bytes=b"trusted"
        )
        relative_path = publish["artifact_metadata"]["relative_path"]
        artifact_path = artifact_root / relative_path
        artifact_path.write_bytes(b"tampered")
        corrupted = client.get(f"/skills/{skill_id}/1.0.0")

    assert corrupted.status_code == 500
    assert corrupted.json()["error"]["code"] == "INTEGRITY_CHECK_FAILED"
