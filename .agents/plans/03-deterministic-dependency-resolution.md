# Plan 03 — Deterministic Dependency Resolution

## Goal
Resolve transitive dependencies into a deterministic `ResolvedBundle` with traceable selection output for downstream resolver clients.

## Stack Alignment
- Runtime: Python 3.12+
- API and contracts: FastAPI + Pydantic v2
- Data layer: SQLAlchemy 2.0 + Alembic
- Database: PostgreSQL from milestone 1 (SQLite optional for isolated local tests only)

## Scope
- Add relationship modeling for `depends_on` and `extends`.
- Implement graph traversal and cycle detection.
- Implement deterministic ordering rule.
- Generate `ResolutionReport` with dependency tree and selected list.
- Provide bundle/report retrieval contract for resolver consumption.
- Exclude prompt parsing and plugin-chain logic (resolver scope).

## Architecture Impact
- Implements core resolution engine in domain layer.
- Expands intelligence layer usage for graph-driven resolution.

## Deliverables
- Endpoint: `POST /resolve` (v1 path alias allowed).
- Endpoint: `GET /bundles/{bundle_id}` (v1 path alias allowed).
- Endpoint: `GET /reports/{resolution_id}` (v1 path alias allowed).
- Relationship edges table and resolver service.
- Types: `ResolvedBundle` and `ResolutionReport`.
- Deterministic ordering rule documentation.
- Learning note on topological sort and deterministic tie-breaking.

## Acceptance Criteria
- Same request and same repo state always return identical bundle ordering.
- Cyclic dependencies fail with clear deterministic error semantics.
- Missing dependency references fail with an explainable report.
- `resolve` p95 <= 250 ms for bundles up to 200 nodes and graph depth <= 5.

## Test Plan
- Golden tests for stable bundle and report output.
- Cycle graph test cases.
- Missing dependency test cases.
- Property-style test: repeated runs produce byte-identical ordering.
- Performance test for p95 latency target under representative graph size.
