"""Shared version-list ordering and default-selection helpers."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Protocol

from app.core.governance import LifecycleStatus

_VISIBLE_DEFAULT_LIFECYCLES: tuple[LifecycleStatus, ...] = ("published", "deprecated")
_LIST_LIFECYCLE_PRIORITY: dict[LifecycleStatus, int] = {
    "published": 0,
    "deprecated": 1,
    "archived": 2,
}


class OrderedVersionLike(Protocol):
    """Minimal shape needed for version-list ordering and default selection."""

    version: str
    lifecycle_status: LifecycleStatus
    published_at: datetime


def sort_versions_for_listing[TOrderedVersion: OrderedVersionLike](
    versions: Iterable[TOrderedVersion],
) -> tuple[TOrderedVersion, ...]:
    """Return versions in the canonical identity-list order."""
    return tuple(
        sorted(
            versions,
            key=lambda item: (
                _LIST_LIFECYCLE_PRIORITY[item.lifecycle_status],
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
