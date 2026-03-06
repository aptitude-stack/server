# app.audit module

Audit infrastructure adapters.

## Purpose

Implements core audit contracts and persists domain audit events durably.

## Key Files

- `recorder.py`: `SQLAlchemyAuditRecorder`, concrete implementation of `AuditPort`.
- `__init__.py`: package marker.

## Contracts

- Implements `app.core.ports.AuditPort`.
- Writes to `AuditEvent` ORM model via SQLAlchemy sessions.

## Notes

This package currently contains one adapter and is intentionally small.
