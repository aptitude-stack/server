"""Regression coverage for Docker release Make targets."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.unit
def test_docker_build_push_bootstraps_and_uses_named_builder() -> None:
    result = subprocess.run(
        [
            "make",
            "-n",
            "docker-build-push",
            "DOCKER_BUILDER=ci-builder",
            "DOCKER_IMAGE=example/image",
            "DOCKER_TAG=test",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert (
        "docker buildx inspect ci-builder >/dev/null 2>&1 || "
        "docker buildx create --name ci-builder --driver docker-container >/dev/null"
        in result.stdout
    )
    assert "docker buildx inspect --bootstrap ci-builder >/dev/null" in result.stdout
    assert (
        "docker buildx build --builder ci-builder --platform linux/amd64,linux/arm64 "
        "--push -t example/image:test ."
        in result.stdout
    )
