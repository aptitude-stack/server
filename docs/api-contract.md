# API Contract

This document describes the current public HTTP contract implemented by `aptitude-server`.
It is a human-readable companion to the pinned OpenAPI artifact at
[`docs/openapi/repository-api-v1.json`](./openapi/repository-api-v1.json).

## Scope

The API is registry-first and intentionally narrow:

- Server-owned behavior: immutable publish, candidate discovery, exact direct dependency reads, exact immutable fetch, lifecycle governance, and audit.
- Client-owned behavior: prompt interpretation, reranking, final selection, dependency solving, lock generation, and execution planning.

The public path boundary is:

- `GET /healthz`
- `GET /readyz`
- `POST /discovery`
- `GET /resolution/{slug}/{version}`
- `POST /fetch/metadata:batch`
- `POST /fetch/content:batch`
- `POST /skill-versions`
- `PATCH /skills/{slug}/versions/{version}/status`

## Auth

Health endpoints do not require authentication.

All other endpoints require `Authorization: Bearer <token>`.

The server enforces scopes through the Bearer token:

- `read`: discovery, resolution, and fetch routes
- `publish`: immutable version publication
- `admin`: lifecycle status updates and admin-only governance behavior

Auth failures use the standard error envelope with these common codes:

- `AUTHENTICATION_REQUIRED`
- `INVALID_AUTH_TOKEN`
- `INSUFFICIENT_SCOPE`

## Error Envelope

All JSON errors use the same shape:

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Request validation failed.",
    "details": {
      "errors": []
    }
  }
}
```

Common status patterns:

- `401`: missing or invalid Bearer token
- `403`: insufficient scope or governance policy violation
- `404`: exact immutable coordinate not found
- `409`: duplicate immutable publish
- `422`: request validation failure
- `500`: persistence failure during publish

## Contract Summary

| Method | Path | Auth | Success | Purpose |
| --- | --- | --- | --- | --- |
| `GET` | `/healthz` | none | `200` | Process liveness probe |
| `GET` | `/readyz` | none | `200` or `503` | Dependency readiness probe |
| `POST` | `/skill-versions` | `publish` | `201` | Publish one immutable skill version |
| `POST` | `/discovery` | `read` | `200` | Return ordered candidate slugs |
| `GET` | `/resolution/{slug}/{version}` | `read` | `200` | Return authored direct `depends_on` selectors |
| `POST` | `/fetch/metadata:batch` | `read` | `200` | Return ordered immutable metadata results |
| `POST` | `/fetch/content:batch` | `read` | `200` | Return ordered immutable markdown parts |
| `PATCH` | `/skills/{slug}/versions/{version}/status` | `admin` | `200` | Transition immutable lifecycle state |

## Shared Data Shapes

### Coordinate

Exact immutable coordinates use:

```json
{
  "slug": "python.lint",
  "version": "1.2.3"
}
```

- `slug`: stable public identifier
- `version`: exact immutable semantic version

### Metadata Envelope

Publish and metadata batch fetch return the same immutable metadata envelope:

```json
{
  "slug": "python.lint",
  "version": "1.2.3",
  "version_checksum": {"algorithm": "sha256", "digest": "..."},
  "content": {
    "checksum": {"algorithm": "sha256", "digest": "..."},
    "size_bytes": 123,
    "rendered_summary": "Lint Python files consistently."
  },
  "metadata": {
    "name": "Python Lint",
    "description": "Linting skill",
    "tags": ["python", "lint"],
    "headers": {"runtime": "python"},
    "inputs_schema": {"type": "object"},
    "outputs_schema": {"type": "object"},
    "token_estimate": 128,
    "maturity_score": 0.9,
    "security_score": 0.95
  },
  "lifecycle_status": "published",
  "trust_tier": "internal",
  "provenance": {
    "repo_url": "https://github.com/example/skills",
    "commit_sha": "aabbccddeeff00112233445566778899aabbccdd",
    "tree_path": "skills/python.lint"
  },
  "published_at": "2026-03-10T08:30:00Z"
}
```

## Endpoints

### `GET /healthz`

Returns lightweight liveness.

Success body:

```json
{
  "status": "ok",
  "service": "aptitude-server",
  "environment": "dev"
}
```

### `GET /readyz`

Returns readiness for backing dependencies.

Success body:

```json
{
  "status": "ready",
  "checks": [
    {
      "name": "database",
      "status": "ok",
      "detail": null
    }
  ]
}
```

If the service is not ready, the same body shape is returned with HTTP `503` and
`status: "not_ready"`.

### `POST /skill-versions`

Publishes one immutable `slug@version`.

Request body sections:

- `slug`, `version`: immutable identity
- `content`: markdown body and optional rendered summary
- `metadata`: name, description, tags, flexible JSON headers, input/output schemas, and optional ranking fields
- `governance`: `trust_tier` plus optional provenance
- `relationships`: authored `depends_on`, `extends`, `conflicts_with`, and `overlaps_with`

Notes:

- `depends_on` items must provide exactly one of `version` or `version_constraint`.
- `internal` publish requires provenance and `publish` scope.
- `verified` publish requires provenance and `admin` scope.
- Successful publish returns the immutable metadata envelope, not embedded relationships or markdown content.

Representative request:

```json
{
  "slug": "python.lint",
  "version": "1.2.3",
  "content": {
    "raw_markdown": "# Python Lint\n\nLint Python files consistently.\n",
    "rendered_summary": "Lint Python files consistently."
  },
  "metadata": {
    "name": "Python Lint",
    "description": "Linting skill",
    "tags": ["python", "lint"]
  },
  "governance": {
    "trust_tier": "internal",
    "provenance": {
      "repo_url": "https://github.com/example/skills",
      "commit_sha": "aabbccddeeff00112233445566778899aabbccdd",
      "tree_path": "skills/python.lint"
    }
  },
  "relationships": {
    "depends_on": [
      {
        "slug": "python.base",
        "version_constraint": ">=1.0.0,<2.0.0"
      }
    ],
    "extends": [],
    "conflicts_with": [],
    "overlaps_with": []
  }
}
```

Notable error codes:

- `DUPLICATE_SKILL_VERSION`
- `CONTENT_STORAGE_FAILURE`
- `POLICY_PUBLISH_FORBIDDEN`
- `POLICY_PROVENANCE_REQUIRED`

### `POST /discovery`

Returns ordered candidate `slug` values only.

Request:

```json
{
  "name": "Python Lint",
  "description": "Lint Python files consistently",
  "tags": ["python", "lint"]
}
```

Response:

```json
{
  "candidates": [
    "python.lint",
    "python.format"
  ]
}
```

Semantics:

- Discovery is candidate generation only.
- It does not choose a final candidate.
- It does not solve dependencies.
- It does not return versions or non-slug cards.
- It searches indexed slug, name, description, and tags.
- With the default policy, discovery returns only `published` versions.

### `GET /resolution/{slug}/{version}`

Returns only the authored direct `depends_on` declarations for one exact immutable version.

Response:

```json
{
  "slug": "python.lint",
  "version": "1.2.3",
  "depends_on": [
    {
      "slug": "python.base",
      "version_constraint": ">=1.0.0,<2.0.0",
      "optional": true,
      "markers": ["linux", "gpu"]
    }
  ]
}
```

Semantics:

- Exact read only, not search
- No recursion
- No constraint solving
- No transitive expansion
- No `extends`, `conflicts_with`, or `overlaps_with` in the public response

Notable error code:

- `SKILL_VERSION_NOT_FOUND`

### `POST /fetch/metadata:batch`

Returns ordered exact metadata results for a list of coordinates.

Request:

```json
{
  "coordinates": [
    {"slug": "python.lint", "version": "1.2.3"},
    {"slug": "python.missing", "version": "9.9.9"}
  ]
}
```

Response:

```json
{
  "results": [
    {
      "status": "found",
      "coordinate": {"slug": "python.lint", "version": "1.2.3"},
      "item": {
        "slug": "python.lint",
        "version": "1.2.3",
        "metadata": {
          "name": "Python Lint",
          "tags": ["python", "lint"]
        },
        "lifecycle_status": "published",
        "trust_tier": "internal",
        "published_at": "2026-03-10T08:30:00Z"
      }
    },
    {
      "status": "not_found",
      "coordinate": {"slug": "python.missing", "version": "9.9.9"},
      "item": null
    }
  ]
}
```

Semantics:

- Response order matches request order.
- Missing coordinates are represented inline as `not_found`.
- The `item` for `found` entries is the full immutable metadata envelope.

### `POST /fetch/content:batch`

Returns markdown content as `multipart/mixed` in request order.

Request body is the same as metadata batch.

Each part always includes:

- `Content-Type: text/markdown; charset=utf-8`
- `X-Aptitude-Slug`
- `X-Aptitude-Version`
- `X-Aptitude-Status`

Found parts also include:

- `ETag`: immutable content digest
- `Cache-Control: public, immutable`
- `Content-Length`

Semantics:

- Response order matches request order.
- Found parts contain UTF-8 markdown bytes.
- `not_found` parts contain an empty body.

### `PATCH /skills/{slug}/versions/{version}/status`

Transitions lifecycle state for one immutable version.

Request:

```json
{
  "status": "deprecated",
  "note": "Superseded by 2.0.0"
}
```

Response:

```json
{
  "slug": "python.lint",
  "version": "1.2.3",
  "status": "deprecated",
  "trust_tier": "internal",
  "lifecycle_changed_at": "2026-03-11T09:15:00Z",
  "is_current_default": true
}
```

Semantics:

- Requires `admin` scope.
- Lifecycle states are `published`, `deprecated`, and `archived`.
- Exact reads allow `published` and `deprecated` for read callers.
- `archived` exact reads are admin-only.

Notable error codes:

- `SKILL_VERSION_NOT_FOUND`
- `POLICY_STATUS_TRANSITION_FORBIDDEN`

## Governance Defaults

The built-in default profile currently behaves as follows:

- Trust tiers: `untrusted`, `internal`, `verified`
- Publish requirements:
  - `untrusted`: `publish`
  - `internal`: `publish` plus provenance
  - `verified`: `admin` plus provenance
- Discovery visibility:
  - default route behavior: `published`
  - internal trust tier can still appear if it is published
- Exact read visibility:
  - `published`: readable with `read`
  - `deprecated`: readable with `read`
  - `archived`: readable with `admin`

## Canonical Sources

For implementation truth, use:

- [`app/main.py`](../app/main.py) for app metadata and mounted routes
- [`app/interface/api`](../app/interface/api/README.md) for route intent
- [`app/interface/dto/skills.py`](../app/interface/dto/skills.py) for request and response DTOs
- [`app/interface/dto/examples.py`](../app/interface/dto/examples.py) for example payloads
- [`docs/openapi/repository-api-v1.json`](./openapi/repository-api-v1.json) for the pinned machine-readable contract
