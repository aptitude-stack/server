"""Shared version-list ordering and default-selection helpers."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Protocol

_VISIBLE_DEFAULT_LIFECYCLES = frozenset(("published", "deprecated"))


class OrderedVersionLike(Protocol):
    """Minimal shape needed for version-list ordering and default selection."""

    @property
    def version(self) -> str: ...

    @property
    def lifecycle_status(self) -> str: ...

    @property
    def published_at(self) -> datetime: ...


def _lifecycle_priority(lifecycle_status: str) -> int:
    if lifecycle_status == "published":
        return 0
    if lifecycle_status == "deprecated":
        return 1
    return 2


def sort_versions_for_listing[TOrderedVersion: OrderedVersionLike](
    versions: Iterable[TOrderedVersion],
) -> tuple[TOrderedVersion, ...]:
    """Return versions in the canonical identity-list order."""
    return tuple(
        sorted(
            versions,
            key=lambda item: (
                _lifecycle_priority(item.lifecycle_status),
                -item.published_at.timestamp(),
                item.version,
            ),
        )
    )


def select_current_default_version[TOrderedVersion: OrderedVersionLike](
    versions: Iterable[TOrderedVersion],
) -> TOrderedVersion | None:
    """Return the current-default version from a sequence of visible versions."""
    return next(
        (
            item
            for item in sort_versions_for_listing(versions)
            if item.lifecycle_status in _VISIBLE_DEFAULT_LIFECYCLES
        ),
        None,
    )
