"""Audit recording adapters.

This module provides infrastructure-level implementations of ``AuditPort``.
Its role is to persist domain audit events to durable storage (SQLAlchemy/DB),
keeping the application layer decoupled from ORM details.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session, sessionmaker

from app.core.ports import AuditPort
from app.persistence.models.audit_event import AuditEvent


class SQLAlchemyAuditRecorder(AuditPort):
    """Store audit events in the database using SQLAlchemy sessions.

    This adapter is the concrete implementation of ``AuditPort`` for relational
    persistence. It creates a short-lived session per call so writes are
    isolated and transaction boundaries stay explicit.
    """

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        """Initialize the recorder with a SQLAlchemy session factory.

        Args:
            session_factory: Callable/factory that returns a new ``Session``.
                A fresh session is used for each recorded event.
        """
        self._session_factory = session_factory

    def record_event(self, *, event_type: str, payload: dict[str, Any] | None = None) -> None:
        """Persist a single audit event.

        Args:
            event_type: Stable event name (for example ``"skill.executed"``).
            payload: Optional structured metadata stored with the event.
                Should be JSON-serializable for reliable persistence.
        """
        # Context manager ensures session cleanup even if commit raises.
        with self._session_factory() as session:
            audit_event = AuditEvent(event_type=event_type, payload=payload)
            session.add(audit_event)
            # Explicit commit makes this write durable as its own transaction.
            session.commit()
