# VendorCheck v1 — Schema Rationale & Migration Guide

## Schema Rationale

This schema targets **Amazon RDS PostgreSQL 16** and is designed for a **pooled multi-tenant B2B SaaS** where every customer (tenant) shares the same database, isolated via `tenant_id` columns and PostgreSQL Row Level Security (RLS).

### Key design decisions

| Decision | Rationale |
|----------|-----------|
| **UUID primary keys** | Globally unique, safe for distributed ID generation, no sequential enumeration risk. Generated via `gen_random_uuid()` (pgcrypto). |
| **`tenant_id` on every tenant-owned table** | Enables RLS policies. The `users` table is the exception — users can belong to multiple tenants via `memberships`. |
| **`TIMESTAMPTZ` everywhere** | Never naive timestamps. All times stored in UTC, displayed in user's local timezone by the app. |
| **`updated_at` triggers** | Automatic via `trigger_set_updated_at()`. The app doesn't need to set `updated_at` manually. |
| **Enum types for constrained values** | `verdict_type`, `document_status`, `check_status`, `decision_type`, `signal_severity`, `alert_type`, `workflow_status`, `review_task_status`, `document_type`, `user_role`. Enforced at the DB level. |
| **CHECK constraints** | `risk_score` constrained to 0–100. `confidence` constrained to 0.0–1.0. `file_size_bytes >= 0`. `version_no >= 1`. |
| **JSONB for flexible payloads** | `metadata` on vendors, `raw_response` on validation_results, `details` on audit_logs, `metadata` on risk_signals and metric_events. |
| **No soft deletes** | MVP simplicity. Hard deletes with `ON DELETE CASCADE` propagation. Add soft-delete later if compliance requires it. |
| **`check_requests` as a standalone table** | Supports the "paste text → analyze → decide" flow alongside the document pipeline. Both flows produce `risk_signals` and can trigger `review_tasks`. |
| **Deferred FKs for circular refs** | `risk_signals` and `review_tasks` reference both `document_versions` and `check_requests`. Since `check_requests` is defined after them, constraints are added via `ALTER TABLE`. |

### Table count: 16

| # | Table | Purpose | Has `tenant_id` |
|---|-------|---------|:---:|
| 1 | `tenants` | Customer workspaces | `id` is the tenant |
| 2 | `users` | Cognito-linked user profiles | No (cross-tenant) |
| 3 | `memberships` | User ↔ Tenant with role | Yes |
| 4 | `vendors` | Vendor profiles per tenant | Yes |
| 5 | `documents` | Document records | Yes |
| 6 | `document_versions` | Versioned uploads per document | Yes |
| 7 | `document_artifacts` | OCR outputs, extracted text | Yes |
| 8 | `extracted_fields` | Structured data from documents | Yes |
| 9 | `validation_results` | LLM/rule-engine analysis output | Yes |
| 10 | `risk_signals` | Individual risk flags | Yes |
| 11 | `review_tasks` | Human review queue items | Yes |
| 12 | `check_requests` | Paste-text check flow | Yes |
| 13 | `alerts` | Notifications per tenant | Yes |
| 14 | `workflow_runs` | Step Functions execution tracking | Yes |
| 15 | `audit_logs` | Immutable action log | Yes |
| 16 | `metric_events` | ROI and usage events | Yes |

---

## How This Maps to FastAPI Models

The SQLAlchemy ORM models in `apps/api/app/models/orm.py` mirror this schema 1:1. Each table has a corresponding class:

| SQL Table | ORM Class | Notes |
|-----------|-----------|-------|
| `tenants` | `Tenant` | Relationships: `memberships`, `vendors` |
| `users` | `User` | Relationships: `memberships`. Keyed by `cognito_sub`. |
| `memberships` | `Membership` | Junction table. Unique on `(tenant_id, user_id)`. |
| `vendors` | `Vendor` | Relationships: `tenant`, `documents` |
| `documents` | `Document` | Relationships: `vendor`, `versions` |
| `document_versions` | `DocumentVersion` | Relationships: `document` |
| `document_artifacts` | `DocumentArtifact` | — |
| `extracted_fields` | `ExtractedField` | — |
| `validation_results` | `ValidationResult` | `raw_response` stored as JSON text in SQLite tests, JSONB in Postgres |
| `risk_signals` | `RiskSignal` | Relationships: `check_request` |
| `review_tasks` | `ReviewTask` | — |
| `check_requests` | `CheckRequest` | Relationships: `signals` |
| `alerts` | `Alert` | — |
| `workflow_runs` | `WorkflowRun` | — |
| `audit_logs` | `AuditLog` | `details` as JSONB, `ip_address` as INET |
| `metric_events` | `MetricEvent` | — |

### ORM portability layer

The ORM uses `Text` columns (not `PG_UUID`) so that unit tests can run against SQLite. In production (RDS), the database enforces UUID via `gen_random_uuid()` defaults. The ORM generates UUIDs via `uuid.uuid4()` in Python.

### Auth flow (Cognito → ORM)

1. Frontend obtains a JWT from Cognito (`amazon-cognito-identity-js`).
2. FastAPI `auth.py` validates the JWT and extracts `sub` (Cognito user ID).
3. The backend looks up `users` by `cognito_sub`. If not found, auto-creates the user.
4. Membership lookup resolves the user's tenant(s) and role.
5. `SET LOCAL 'app.tenant_id' = '<uuid>'` is issued on the DB session for RLS.

---

## Tables That Should Get RLS First

RLS is already defined for all 15 tenant-owned tables. However, **enforcement priority** for testing and hardening should be:

### Tier 1 — Must-verify first (direct user data exposure risk)

| Table | Why |
|-------|-----|
| `check_requests` | Contains raw vendor text, bank details (masked), verdicts. Highest sensitivity. |
| `vendors` | Contains PII (email, phone). Cross-tenant leak is a compliance violation. |
| `documents` | Links to S3 objects. Leaking document metadata exposes file structure. |
| `document_versions` | Contains S3 keys. A leaked key + bucket = unauthorized file access. |

### Tier 2 — High value

| Table | Why |
|-------|-----|
| `extracted_fields` | Contains field values extracted from documents (bank numbers, names). |
| `review_tasks` | Exposes internal review decisions across tenants. |
| `risk_signals` | Reveals risk analysis details. |
| `alerts` | Tenant-specific notifications. |

### Tier 3 — Operational

| Table | Why |
|-------|-----|
| `validation_results` | Analysis outputs — less directly sensitive. |
| `document_artifacts` | OCR artifacts — derived data, less PII. |
| `workflow_runs` | Internal execution tracking. |
| `audit_logs` | Sensitive for compliance but append-only. |
| `metric_events` | Usage metrics. |
| `memberships` | Role assignments. |
| `tenants` | Already scoped by `id = app_tenant_id()`. |

---

## Migration Notes from Supabase-Era Schema

The original VendorCheck design documents referenced Supabase for auth and database hosting. The codebase has been migrated to AWS. Here is what changed and what to watch for:

### What was removed

| Supabase concept | AWS replacement | Status |
|-----------------|-----------------|--------|
| Supabase Auth (GoTrue) | Amazon Cognito | Done. `cognito_sub` on `users` table, JWT validation via Cognito JWKS. |
| `auth.users` built-in table | `users` table with `cognito_sub` FK | Done. No dependency on Supabase `auth` schema. |
| Supabase JS SDK (`@supabase/supabase-js`) | `amazon-cognito-identity-js` + custom `lib/api.ts` | Done. Frontend auth uses Cognito SDK. |
| Supabase PostgREST | FastAPI REST API | Done. No PostgREST dependency. |
| Supabase Storage | Amazon S3 | Done. `s3_bucket` + `s3_key` on `document_versions` and `document_artifacts`. |
| `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` env vars | `COGNITO_USER_POOL_ID`, `COGNITO_USER_POOL_CLIENT_ID`, `DATABASE_URL` | Done. `.env.example` updated. |

### What to verify in FastAPI models and services

1. **No `supabase` import anywhere in backend code.** The `supabase` Python package is listed in `pyproject.toml` as a legacy dependency. It should be removed once confirmed unused.
2. **`auth.py`** must validate Cognito JWTs only, not Supabase JWTs. Check that JWKS URL points to `https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/jwks.json`.
3. **`config.py`** should not reference `supabase_url` or `supabase_service_role_key` as required fields. They may still be listed as optional for migration compat — remove when ready.
4. **RLS tenant resolution** uses `SET LOCAL 'app.tenant_id'` on the PostgreSQL session. This is database-native and has no Supabase dependency.
5. **User creation flow:** On first login, the backend creates a `users` row from the Cognito JWT claims (`sub`, `email`, `name`). This replaces the old pattern where Supabase Auth auto-populated `auth.users`.

### Old assumptions to remove

- **`auth.uid()` in RLS policies**: The old Supabase pattern used `auth.uid()` to get the current user from JWT claims stored by PostgREST. The new pattern uses `app_tenant_id()` which reads from a session variable set by the FastAPI middleware. No `auth` schema dependency.
- **`auth.users` joins**: Any query that joined against Supabase's built-in `auth.users` table must use the `users` table instead.
- **Supabase realtime subscriptions**: Not applicable. Use SNS for notifications and polling/WebSocket from FastAPI if needed.
- **Supabase Edge Functions**: Replaced by AWS Lambda + Step Functions.
