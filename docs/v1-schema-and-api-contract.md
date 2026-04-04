# VendorCheck v1 — Database Schema & API Contract

**Status:** Final specification — pre-implementation  
**Date:** 2026-04-04 (revised 2026-04-04)  
**Author:** Backend architecture pass  

---

## 1. Known Facts Used

| # | Fact | Source |
|---|------|--------|
| 1 | Product is VendorCheck — AI trust/verification inbox for SMB payments | Locked decisions |
| 2 | v1 use case: vendor bank-change request verification | Locked decisions |
| 3 | Primary persona: finance manager / controller at 10–50 person company | Locked decisions |
| 4 | Target niche: property managers | Locked decisions |
| 5 | Stack: Supabase Postgres + Supabase Storage + Supabase Auth + FastAPI | Locked decisions |
| 6 | Auth: email/password with email verification from day one | Locked decisions |
| 7 | Tenancy: 1 owner + up to 2 teammates per workspace for beta | Locked decisions |
| 8 | Input types: pasted text or digitally generated PDF | Locked decisions |
| 9 | Verdicts: Safe / Verify / Blocked | Locked decisions |
| 10 | Decisions: Approve / Hold / Reject | Locked decisions |
| 11 | Roles: Admin (workspace mgmt), Reviewer (full decision), Member (submit + review, no approve) | Locked decisions |
| 12 | Sensitive data: hashed/tokenized comparisons, masked display, no raw bank numbers in app model | Locked decisions |
| 13 | Storage boundary: Postgres = extracted/derived data + metadata; Supabase Storage = raw files | Locked decisions |
| 14 | Workspace visibility: shared, with role-based action permissions | Locked decisions |
| 15 | Budget: ~$20–30/month (inference + infra) | Locked decisions |
| 16 | AI provider: OpenAI first | Locked decisions |
| 17 | Not in v1: payments, AP automation, inbox sync, OCR, mobile, notifications, billing, analytics, Slack | Locked decisions |

---

## 2. Explicit Assumptions

| # | Assumption | Rationale |
|---|-----------|-----------|
| A1 | One workspace per user in v1. A user cannot belong to multiple workspaces simultaneously. | Simplifies auth context, query scoping, and onboarding. Multi-workspace is a v2+ concern. |
| A2 | Workspace is auto-created when the user first calls `GET /api/v1/me` after email verification. No separate workspace-creation endpoint in v1. | Removes an unnecessary API round-trip and removes POST /workspaces from launch scope. Default workspace name derived from the user's display name. The workspace entry and admin membership are created atomically on first `/me` call. |
| A3 | Member addition requires the invitee to already have a Supabase Auth account. No pending-invite system in v1. `workspace_invites` table is deferred. Admin shares the signup URL, then adds the person by email via `POST /workspaces/{id}/members`. | Avoids an invites table. Acceptable for a 1+2 user beta. |
| A4 | Check processing (extraction + AI analysis) is synchronous within the POST /checks request. | With ≤3 users and no concurrent load, a 5–10 second synchronous response is acceptable. Avoids polling/realtime complexity. A loading spinner on the frontend covers the wait. |
| A5 | Decisions are **immutable** once submitted. A check can only receive one decision. Attempting to re-decide returns 409. | Eliminates the need for a decision audit log table in v1. Avoids mutable-decision edge cases. If circumstances change, the user submits a new check. |
| A6 | Vendor identity is derived from `check_requests.vendor_name`, not a separate vendors table. | The inbox already groups by vendor name. A dedicated vendors table adds joins and CRUD without delivering v1 value. Deferred. |
| A7 | PDF text extraction uses a local Python library (e.g., pdfplumber), not an external OCR service. | Digitally generated PDFs have embedded text. No OCR needed. Keeps cost at zero for extraction. |
| A8 | The FastAPI backend connects to Supabase using the **service role key** (bypasses RLS). Authorization is enforced in application code. | Gives the backend full control. RLS can be layered in later as defense-in-depth. |
| A9 | File uploads go to Supabase Storage via the backend (not direct client upload). | Keeps the upload flow simple: one API call creates the check + stores the file. Avoids client-side Storage SDK complexity. |
| A10 | API versioning uses a `/api/v1/` URL prefix. | Simple, explicit, no magic headers. |

---

## 3. Final v1 Domain Model Summary

```
┌─────────────┐       ┌──────────────────┐
│   profiles   │──────▶│  auth.users       │  (Supabase-managed)
└──────┬──────┘       └──────────────────┘
       │
       │ belongs to (1 workspace in v1)
       ▼
┌──────────────────┐
│ workspace_members │◀─── role: admin | reviewer | member
└──────┬───────────┘
       │
       ▼
┌──────────────┐
│  workspaces   │
└──────┬───────┘
       │
       │ scopes
       ▼
┌──────────────────┐      1      ┌───────────────┐
│  check_requests   │─────────────▶│  source_files  │  (0 or 1 per check)
└──────┬───────────┘              └───────────────┘
       │
       │ has many
       ▼
┌──────────────────┐
│  risk_signals     │
└──────────────────┘
```

**Core entities:** 6 tables.  
**Core flow:** User → Workspace → Check Request → [Source File] + Risk Signals → Verdict → Decision.

---

## 4. Launch-Required Tables

| Table | Purpose |
|-------|---------|
| `profiles` | Extends Supabase auth.users with app-specific fields |
| `workspaces` | Tenant/account container |
| `workspace_members` | User ↔ Workspace binding with role |
| `check_requests` | Core entity: submitted vendor verification check |
| `risk_signals` | Individual risk findings from analysis |
| `source_files` | Metadata for uploaded PDFs (actual file in Supabase Storage) |

---

## 5. Deferred Tables

| Table | Why Deferred | When to Add |
|-------|-------------|-------------|
| `vendors` | Vendor identity is derived from `check_requests.vendor_name`. A dedicated table adds joins and CRUD without v1 value. | When vendor profile pages, vendor-level settings, or cross-workspace vendor records are needed. |
| `workspace_invites` | No pending-invite flow in v1. Invitee must sign up first; admin then adds by email. | When self-serve invite flows (email-before-signup) are required. |
| `decision_audit_log` | Decisions are immutable in v1 — no audit log is needed. A single decision per check is stored on the check row. | When mutable decisions or compliance-level audit trails are scoped. |
| `check_request_comparisons` | Comparison is derived at analysis time from `prior_check_id`. Storing rows adds schema complexity without v1 value. | When comparison history or cross-check linking is a product feature. |

---

## 6. Table-by-Table Schema Specification

### 6.1 `profiles`

**Purpose:** Application-level user profile extending Supabase `auth.users`.  
**Required for launch?** Yes.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `id` | `uuid` | NO | — | Same value as `auth.users.id` |
| `display_name` | `text` | NO | — | Collected during onboarding or derived from email |
| `created_at` | `timestamptz` | NO | `now()` | |
| `updated_at` | `timestamptz` | NO | `now()` | |

- **Primary key:** `id`
- **Foreign keys:** `id` → `auth.users.id` ON DELETE CASCADE
- **Unique constraints:** None beyond PK.
- **Index suggestions:** None needed (PK covers lookups).
- **Notes:** Created immediately after Supabase Auth signup succeeds (in the same onboarding flow). The profile row is the app's proof that the user completed onboarding. Supabase Auth handles email, password hash, email_verified — none of those are duplicated here.

---

### 6.2 `workspaces`

**Purpose:** Tenant container. All check requests, members, and files are scoped to a workspace.  
**Required for launch?** Yes.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `id` | `uuid` | NO | `gen_random_uuid()` | |
| `name` | `text` | NO | — | e.g., "Acme Property Management" |
| `created_by` | `uuid` | NO | — | The user who created this workspace |
| `created_at` | `timestamptz` | NO | `now()` | |
| `updated_at` | `timestamptz` | NO | `now()` | |

- **Primary key:** `id`
- **Foreign keys:** `created_by` → `auth.users.id`
- **Unique constraints:** None. Multiple workspaces can share a name.
- **Index suggestions:** None needed (low row count in v1).
- **Notes:** Created once during onboarding. The creator is automatically added as `admin` in `workspace_members`. v1 enforces max 1 workspace per user at the application level.

---

### 6.3 `workspace_members`

**Purpose:** Maps users to workspaces with a role.  
**Required for launch?** Yes.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `id` | `uuid` | NO | `gen_random_uuid()` | |
| `workspace_id` | `uuid` | NO | — | |
| `user_id` | `uuid` | NO | — | |
| `role` | `text` | NO | — | Enum: `admin`, `reviewer`, `member` |
| `joined_at` | `timestamptz` | NO | `now()` | |

- **Primary key:** `id`
- **Foreign keys:** `workspace_id` → `workspaces.id` ON DELETE CASCADE, `user_id` → `auth.users.id` ON DELETE CASCADE
- **Unique constraints:** `(workspace_id, user_id)` — a user can only appear once per workspace.
- **Index suggestions:** `(user_id)` — for looking up a user's workspace on every authenticated request.
- **Notes:** The user who creates the workspace gets role=`admin`. Max 3 members per workspace enforced at application level for beta. Role is checked on every mutating API call.

---

### 6.4 `check_requests`

**Purpose:** Core entity. Represents one vendor verification check: input, extracted data, analysis, verdict, and decision.  
**Required for launch?** Yes.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `id` | `uuid` | NO | `gen_random_uuid()` | |
| `workspace_id` | `uuid` | NO | — | Scoping |
| `submitted_by` | `uuid` | NO | — | The user who submitted this check |
| `input_type` | `text` | NO | — | Enum: `paste_text`, `pdf` |
| `raw_input_text` | `text` | NO | — | Pasted text verbatim, or text extracted from PDF |
| `vendor_name` | `text` | YES | — | Extracted by AI. Null if extraction failed. |
| `vendor_contact_email` | `text` | YES | — | Extracted. Nullable. |
| `vendor_contact_phone` | `text` | YES | — | Extracted. Nullable. |
| `bank_name` | `text` | YES | — | Extracted. Nullable. |
| `bank_account_hash` | `text` | YES | — | SHA-256 of normalized account number. For comparison only. |
| `bank_routing_hash` | `text` | YES | — | SHA-256 of normalized routing number. For comparison only. |
| `bank_account_masked` | `text` | YES | — | Display-safe format, e.g., `****1234` |
| `bank_routing_masked` | `text` | YES | — | Display-safe format, e.g., `****5678` |
| `status` | `text` | NO | `'processing'` | Enum: `processing`, `analyzed`, `error` |
| `verdict` | `text` | YES | — | Enum: `safe`, `verify`, `blocked`. Null until analyzed. |
| `verdict_explanation` | `text` | YES | — | Human-readable explanation from AI |
| `recommended_action` | `text` | YES | — | What the user should do next |
| `risk_score` | `integer` | YES | — | 0–100 composite score. Null until analyzed. |
| `prior_check_id` | `uuid` | YES | — | Self-FK: the most recent previous check for same vendor_name in this workspace. Enables "compared to" UI. |
| `bank_details_changed` | `boolean` | YES | — | True if hashes differ from prior_check. Null if no prior check exists. |
| `analysis_error` | `text` | YES | — | Error message if status=`error` |
| `decision` | `text` | YES | — | Enum: `approved`, `held`, `rejected`. Null until decided. |
| `decided_by` | `uuid` | YES | — | Who made the decision |
| `decided_at` | `timestamptz` | YES | — | When the decision was made |
| `decision_note` | `text` | YES | — | Optional note from the decider |
| `created_at` | `timestamptz` | NO | `now()` | |
| `updated_at` | `timestamptz` | NO | `now()` | |

- **Primary key:** `id`
- **Foreign keys:**
  - `workspace_id` → `workspaces.id`
  - `submitted_by` → `auth.users.id`
  - `decided_by` → `auth.users.id`
  - `prior_check_id` → `check_requests.id` (self-referencing, nullable)
- **Unique constraints:** None. The same vendor can have multiple checks.
- **Index suggestions:**
  - `(workspace_id, created_at DESC)` — inbox listing, default sort
  - `(workspace_id, vendor_name)` — vendor history lookup for comparison
  - `(workspace_id, status)` — filtering by processing state
  - `(workspace_id, verdict)` — filtering by verdict
- **Notes:**
  - `raw_input_text` stores the user's original input. This MAY contain bank numbers in freeform text. Access is controlled at the application level; this field is never exposed in list endpoints, only in the detail view.
  - `bank_account_hash` / `bank_routing_hash` are computed server-side during extraction. The raw numbers are NEVER stored in any Postgres column. They exist only transiently in memory during the extraction step.
  - `prior_check_id` is populated at analysis time by querying: "most recent analyzed check_request with same vendor_name in this workspace." This is a convenience FK for the detail UI.
  - `bank_details_changed` is derived during analysis by comparing hashes against `prior_check_id`. Stored as a boolean to avoid re-computation on read.

---

### 6.5 `risk_signals`

**Purpose:** Individual risk findings produced during analysis. Multiple signals per check request.  
**Required for launch?** Yes.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `id` | `uuid` | NO | `gen_random_uuid()` | |
| `check_request_id` | `uuid` | NO | — | |
| `signal_type` | `text` | NO | — | Controlled value (see Enums section) |
| `severity` | `text` | NO | — | Enum: `low`, `medium`, `high`, `critical` |
| `title` | `text` | NO | — | Short human-readable label, e.g., "Bank details changed" |
| `description` | `text` | NO | — | Explanation of this signal |
| `metadata` | `jsonb` | YES | — | Signal-type-specific data (see notes) |
| `created_at` | `timestamptz` | NO | `now()` | |

- **Primary key:** `id`
- **Foreign keys:** `check_request_id` → `check_requests.id` ON DELETE CASCADE
- **Unique constraints:** None. Multiple signals of the same type per check are allowed.
- **Index suggestions:** `(check_request_id)` — for fetching all signals for a check.
- **Notes:**
  - `metadata` is a JSONB column to handle signal-type-specific data without adding columns for every signal variant. Example: for `bank_change_detected`, metadata might contain `{ "field": "account_number", "previous_masked": "****5678", "current_masked": "****1234" }`. This is the ONE justified use of JSON in the schema — signal types will evolve and adding columns for each would require migrations.
  - Signals are INSERT-only. They are never updated or deleted independently. If a check is re-analyzed (future), signals are deleted and recreated via CASCADE.

---

### 6.6 `source_files`

**Purpose:** Metadata for uploaded PDF files. The actual binary lives in Supabase Storage.  
**Required for launch?** Yes.

| Column | Type | Nullable | Default | Notes |
|--------|------|----------|---------|-------|
| `id` | `uuid` | NO | `gen_random_uuid()` | |
| `check_request_id` | `uuid` | NO | — | |
| `storage_path` | `text` | NO | — | Path within Supabase Storage bucket, e.g., `checks/{workspace_id}/{check_id}/{filename}` |
| `original_filename` | `text` | NO | — | As uploaded by the user |
| `mime_type` | `text` | NO | — | Must be `application/pdf` for v1 |
| `file_size_bytes` | `integer` | NO | — | |
| `created_at` | `timestamptz` | NO | `now()` | |

- **Primary key:** `id`
- **Foreign keys:** `check_request_id` → `check_requests.id` ON DELETE CASCADE
- **Unique constraints:** `(check_request_id)` — one file per check in v1.
- **Index suggestions:** None needed (accessed via check_request_id FK).
- **Notes:**
  - Storage bucket name: `check-files` (private bucket, no public access).
  - Storage path pattern: `{workspace_id}/{check_request_id}/{original_filename}` — ensures workspace isolation at the storage level.
  - The backend generates a signed URL when the frontend needs to display or download the file. Signed URLs expire after 5 minutes.

---

## 7. Enums and Controlled Values

### 7.1 Roles — `workspace_members.role`

| Value | Description |
|-------|-------------|
| `admin` | Workspace management, all actions. Auto-assigned to workspace creator. |
| `reviewer` | Submit checks, review, approve, hold, reject. |
| `member` | Submit checks, review. Cannot approve. |

### 7.2 Input Type — `check_requests.input_type`

| Value | Description |
|-------|-------------|
| `paste_text` | User pasted freeform text |
| `pdf` | User uploaded a digitally generated PDF |

### 7.3 Check Status — `check_requests.status`

| Value | Description |
|-------|-------------|
| `processing` | Submitted, analysis in progress (transient in sync model) |
| `analyzed` | Analysis complete, verdict available |
| `error` | Analysis failed |

### 7.4 Verdict — `check_requests.verdict`

| Value | Description |
|-------|-------------|
| `safe` | Low risk. Proceed normally. |
| `verify` | Medium risk. Manual verification recommended. |
| `blocked` | High risk. Do not proceed without escalation. |

### 7.5 Decision — `check_requests.decision`

| Value | Description |
|-------|-------------|
| `approved` | User approved the vendor change |
| `held` | User placed a hold for further review |
| `rejected` | User rejected the vendor change |

### 7.6 Signal Severity — `risk_signals.severity`

| Value | Description |
|-------|-------------|
| `low` | Informational |
| `medium` | Worth reviewing |
| `high` | Likely problematic |
| `critical` | Strong fraud indicator |

### 7.7 Signal Types — `risk_signals.signal_type`

These are not database-enforced enums. They are application-level controlled values that will evolve as the AI analysis improves.

| Value | Description |
|-------|-------------|
| `bank_change_detected` | Bank account or routing number differs from prior check |
| `new_vendor` | No prior checks for this vendor in the workspace |
| `domain_mismatch` | Contact email domain doesn't match vendor name |
| `urgency_language` | Request contains urgency/pressure language |
| `formatting_anomaly` | Document formatting is inconsistent or suspicious |
| `contact_info_changed` | Contact details differ from prior check |
| `missing_fields` | Expected fields could not be extracted |
| `ai_risk_flag` | General LLM-identified risk not covered by other types |

> **Implementation note:** `signal_type` values are defined in application code (a Python enum or constant list), not as a Postgres enum. This avoids migrations when adding new signal types.

---

## 8. Sensitive Data Handling Rules

| Data | Storage Rule | Display Rule |
|------|-------------|--------------|
| Raw bank account number | NEVER stored in any Postgres column. Exists transiently in server memory during extraction, then discarded. | Never displayed. Only the masked version (`****1234`) is shown. |
| Raw routing number | Same as above. | Same as above. |
| `bank_account_hash` | SHA-256 hash stored in `check_requests`. Used for comparison only. | Never displayed to users. Internal use only. |
| `bank_routing_hash` | Same as above. | Same as above. |
| `bank_account_masked` | Stored in `check_requests`. Last 4 digits only. | Displayed in Request Detail UI. |
| `bank_routing_masked` | Same as above. | Same as above. |
| `raw_input_text` | Stored in `check_requests`. May contain bank numbers in freeform text. | Displayed only on the Request Detail screen, never in list views. Access controlled by workspace membership. |
| Uploaded PDF | Stored in Supabase Storage (private bucket). Only metadata in Postgres. | Accessible via time-limited signed URL (5 min expiry). |
| User email | Managed by Supabase Auth. Not duplicated in app tables. | Displayed in workspace member list. Read from Supabase Auth via service role. |
| User password | Managed by Supabase Auth. Never accessible to the application. | Never displayed. |

### Hashing specification

- **Algorithm:** SHA-256
- **Input normalization:** Strip whitespace, remove dashes/spaces, lowercase. Then hash.
- **Salt:** No salt needed. The hash is for same-value comparison within a workspace, not password storage. Two identical account numbers should produce the same hash for comparison to work.

> **Assumption A11:** SHA-256 without salt is acceptable for bank-detail comparison in v1. The hashes are not exposed via any API endpoint and exist solely for server-side comparison logic. If regulatory review later requires stronger isolation, hashing can be upgraded.

---

## 9. Row-Level Access Model

Authorization is enforced in FastAPI application code. The backend uses the Supabase service role key (bypasses Postgres RLS).

### Request authentication flow

1. Frontend sends Supabase JWT in `Authorization: Bearer <token>` header.
2. Backend verifies JWT signature against Supabase JWT secret.
3. Backend extracts `user_id` from token claims.
4. Backend queries `workspace_members` to get `workspace_id` and `role` for this user.
5. If no membership found → 403.
6. All subsequent queries are scoped to `workspace_id`.

### Permission matrix

| Action | Admin | Reviewer | Member |
|--------|-------|----------|--------|
| View workspace + member list | ✓ | ✓ | ✓ |
| Add member (by email) | ✓ | — | — |
| Submit check | ✓ | ✓ | ✓ |
| View check list (inbox) | ✓ | ✓ | ✓ |
| View check detail | ✓ | ✓ | ✓ |
| Approve check | ✓ | ✓ | — |
| Hold check | ✓ | ✓ | ✓ |
| Reject check | ✓ | ✓ | ✓ |
| Download source file | ✓ | ✓ | ✓ |

> **Design choices:**
> - Workspace is auto-created at signup — no UI action needed to create it.
> - Member removal and role changes are deferred. For the 1+2 user beta, these are handled directly via the Supabase dashboard.
> - Members can Hold and Reject but cannot Approve. Only Reviewers and Admins can Approve, restricting payment authorization to trusted roles.

---

## 10. API Resource Model

| Resource | Entity | Base Path |
|----------|--------|-----------|
| Profile | `profiles` | `/api/v1/me` |
| Workspace | `workspaces` | `/api/v1/workspaces` |
| Member | `workspace_members` | `/api/v1/workspaces/{workspace_id}/members` |
| Check | `check_requests` + `risk_signals` + `source_files` | `/api/v1/checks` |
| Decision | embedded in Check | `/api/v1/checks/{check_id}/decision` |
| Source file download | `source_files` | `/api/v1/checks/{check_id}/file` |

> **Note:** Checks are scoped to the authenticated user's workspace. The `workspace_id` is inferred from the JWT — it is NOT in the URL path for check endpoints. This prevents IDOR attacks and simplifies frontend routing.

---

## 11. Endpoint List

| # | Method | Path | Purpose |
|---|--------|------|---------|
| 1 | `GET` | `/api/v1/me` | Get current user profile + workspace context. Auto-creates workspace on first call. |
| 2 | `GET` | `/api/v1/workspaces/{workspace_id}/members` | List workspace members |
| 3 | `POST` | `/api/v1/workspaces/{workspace_id}/members` | Add a member by email (admin only) |
| 4 | `POST` | `/api/v1/checks` | Submit a new check |
| 5 | `GET` | `/api/v1/checks` | List checks (inbox) |
| 6 | `GET` | `/api/v1/checks/{check_id}` | Get check detail with signals |
| 7 | `POST` | `/api/v1/checks/{check_id}/decision` | Log a decision (immutable) |
| 8 | `GET` | `/api/v1/checks/{check_id}/file` | Get signed download URL for source PDF |

**Total: 8 endpoints.**

**Deferred to v2:** `POST /workspaces` (not needed — auto-create), `DELETE /workspaces/{id}/members/{uid}` (admin manages via Supabase dashboard), `PATCH /workspaces/{id}/members/{uid}` (role changes via Supabase dashboard).

---

## 12. Endpoint Contract Details

### 12.1 `GET /api/v1/me`

**Purpose:** Returns authenticated user's profile and workspace context. On first call for a newly verified user, auto-creates their workspace and admin membership atomically.  
**Auth required?** Yes.

**Request body:** None.

**Response body (200):**
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "display_name": "Jane Smith",
    "email_verified": true
  },
  "workspace": {
    "id": "uuid",
    "name": "Jane Smith's Workspace",
    "role": "admin"
  }
}
```

**Success status code:** `200 OK`  
**Error status codes:**
- `401 Unauthorized` — Invalid or missing JWT.
- `403 Forbidden` — JWT valid but email not verified. User must complete email verification before entering the app.

**Notes for v1 simplification:**
- `email` and `email_verified` are read from Supabase Auth via the service role API, not from the profiles table.
- Auto-create logic: if no `workspace_members` row exists for this user, the backend creates a `workspaces` row (name = `"{display_name}'s Workspace"`) and a `workspace_members` row (role = `admin`) in a single transaction, then returns the result.
- `workspace` is never `null` in a successful 200 response. A verified user always has a workspace after the first `/me` call.

---

### 12.2 `GET /api/v1/workspaces/{workspace_id}/members`

**Purpose:** List all members of the workspace.  
**Auth required?** Yes.

**Request body:** None.

**Response body (200):**
```json
{
  "members": [
    {
      "user_id": "uuid",
      "email": "owner@example.com",
      "display_name": "Jane Smith",
      "role": "admin",
      "joined_at": "2026-04-04T12:00:00Z"
    },
    {
      "user_id": "uuid",
      "email": "reviewer@example.com",
      "display_name": "Bob Lee",
      "role": "reviewer",
      "joined_at": "2026-04-05T09:00:00Z"
    }
  ]
}
```

**Success status code:** `200 OK`  
**Error status codes:**
- `401 Unauthorized`
- `403 Forbidden` — User is not a member of this workspace.

**Notes for v1 simplification:** Email is fetched from Supabase Auth by the backend (service role). No pagination needed — max 3 members.

---

### 12.3 `POST /api/v1/workspaces/{workspace_id}/members`

**Purpose:** Add a member to the workspace by email.  
**Auth required?** Yes. **Role required:** `admin`.

**Request body:**
```json
{
  "email": "newuser@example.com",
  "role": "reviewer"
}
```

**Validation:**
- `email`: required, valid email format.
- `role`: required, one of `reviewer`, `member`. (Cannot assign `admin` — only one admin per workspace in v1.)

**Response body (201):**
```json
{
  "user_id": "uuid",
  "email": "newuser@example.com",
  "display_name": "New User",
  "role": "reviewer",
  "joined_at": "2026-04-06T10:00:00Z"
}
```

**Success status code:** `201 Created`  
**Error status codes:**
- `401 Unauthorized`
- `403 Forbidden` — Caller is not `admin`.
- `404 Not Found` — No Supabase Auth user with that email. Response: `{ "error": "user_not_found", "message": "No account found for this email. They must sign up first." }`
- `409 Conflict` — User is already a member of this workspace.
- `422 Unprocessable Entity` — Validation error.
- `429 Too Many Requests` — Workspace already has 3 members (beta limit).

**Notes for v1 simplification:** The backend uses `supabase.auth.admin.list_users()` filtered by email to find the user. If the user belongs to another workspace, the backend returns 409 (v1 enforces single-workspace per user). The 3-member cap is hardcoded. Member removal and role changes are handled via the Supabase dashboard for the beta period.

---

### 12.4 `POST /api/v1/checks`

**Purpose:** Submit a new vendor verification check. This is the core endpoint.  
**Auth required?** Yes. **Role required:** Any role (`admin`, `reviewer`, `member`).

**Content-Type:** `multipart/form-data`

**Request fields:**

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `input_type` | string (form field) | Yes | `paste_text` or `pdf` |
| `raw_text` | string (form field) | Conditional | Required if `input_type=paste_text`. The pasted text. |
| `file` | binary (file upload) | Conditional | Required if `input_type=pdf`. Must be `application/pdf`, max 5MB. |

**Response body (201):**
```json
{
  "id": "uuid",
  "status": "analyzed",
  "input_type": "paste_text",
  "vendor_name": "ABC Plumbing LLC",
  "vendor_contact_email": "billing@abcplumbing.com",
  "bank_name": "Chase",
  "bank_account_masked": "****1234",
  "bank_routing_masked": "****5678",
  "bank_details_changed": true,
  "verdict": "verify",
  "verdict_explanation": "Bank account details differ from the previous request for this vendor. The routing number has changed from a Chase account to a regional bank.",
  "recommended_action": "Contact ABC Plumbing LLC directly using the phone number on file to verify the bank change before processing payment.",
  "risk_score": 65,
  "signals": [
    {
      "id": "uuid",
      "signal_type": "bank_change_detected",
      "severity": "high",
      "title": "Bank details changed",
      "description": "Account number differs from previous check on 2026-03-15."
    },
    {
      "id": "uuid",
      "signal_type": "domain_mismatch",
      "severity": "medium",
      "title": "Email domain mismatch",
      "description": "Contact email uses gmail.com, not abcplumbing.com."
    }
  ],
  "prior_check_id": "uuid-of-previous-check",
  "decision": null,
  "submitted_by": {
    "id": "uuid",
    "display_name": "Jane Smith"
  },
  "created_at": "2026-04-04T14:30:00Z"
}
```

If analysis failed:
```json
{
  "id": "uuid",
  "status": "error",
  "input_type": "paste_text",
  "analysis_error": "AI analysis service unavailable. Please try again.",
  "vendor_name": null,
  "verdict": null,
  "signals": [],
  "decision": null,
  "submitted_by": {
    "id": "uuid",
    "display_name": "Jane Smith"
  },
  "created_at": "2026-04-04T14:30:00Z"
}
```

**Success status code:** `201 Created`  
**Error status codes:**
- `401 Unauthorized`
- `413 Payload Too Large` — File exceeds 5MB.
- `415 Unsupported Media Type` — File is not `application/pdf`.
- `422 Unprocessable Entity` — Missing required fields, or `raw_text` empty, or `input_type` invalid.
- `503 Service Unavailable` — AI service down. The check_request is still saved with `status=error`.

**Notes for v1 simplification:**
- Processing is **synchronous**. The endpoint blocks while extraction + AI analysis runs (5–15 seconds). Frontend shows a loading state.
- If AI analysis fails, the request is still persisted with `status=error` so the user can see it failed. There is no retry mechanism in v1 — the user submits again.
- The `signals` array is included inline in the response (not a separate fetch).
- `bank_account_hash` and `bank_routing_hash` are NEVER included in any API response.
- `raw_input_text` is NOT included in the creation response — only available via GET detail.

**Idempotency:** No built-in idempotency key. Duplicate submissions create separate check_requests. This is acceptable for v1 — the user can see duplicates in the inbox and ignore them. A future version could add an idempotency header.

---

### 12.5 `GET /api/v1/checks`

**Purpose:** List checks for the current workspace (inbox view).  
**Auth required?** Yes.

**Query parameters:**

| Param | Type | Default | Notes |
|-------|------|---------|-------|
| `page` | integer | `1` | 1-indexed |
| `per_page` | integer | `20` | Max 100 |
| `verdict` | string | — | Filter: `safe`, `verify`, `blocked` |
| `status` | string | — | Filter: `analyzed`, `error` |
| `decision` | string | — | Filter: `approved`, `held`, `rejected`, `pending` (`pending` = decision IS NULL) |
| `search` | string | — | Search `vendor_name` (case-insensitive prefix match) |
| `sort` | string | `created_at_desc` | One of: `created_at_desc`, `created_at_asc`, `risk_score_desc` |

**Response body (200):**
```json
{
  "checks": [
    {
      "id": "uuid",
      "vendor_name": "ABC Plumbing LLC",
      "input_type": "paste_text",
      "status": "analyzed",
      "verdict": "verify",
      "risk_score": 65,
      "bank_details_changed": true,
      "decision": null,
      "submitted_by": {
        "id": "uuid",
        "display_name": "Jane Smith"
      },
      "created_at": "2026-04-04T14:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 47,
    "total_pages": 3
  }
}
```

**Success status code:** `200 OK`  
**Error status codes:**
- `401 Unauthorized`
- `422 Unprocessable Entity` — Invalid query parameter values.

**Notes for v1 simplification:** List items do NOT include `signals`, `verdict_explanation`, `recommended_action`, or `raw_input_text`. Those are fetched via the detail endpoint. This keeps the list payload small.

---

### 12.6 `GET /api/v1/checks/{check_id}`

**Purpose:** Full check detail including signals and source file info.  
**Auth required?** Yes.

**Request body:** None.

**Response body (200):**
```json
{
  "id": "uuid",
  "workspace_id": "uuid",
  "input_type": "paste_text",
  "status": "analyzed",
  "raw_input_text": "Hi, this is ABC Plumbing. We've changed our bank...",
  "vendor_name": "ABC Plumbing LLC",
  "vendor_contact_email": "billing@abcplumbing.com",
  "vendor_contact_phone": "555-0123",
  "bank_name": "Chase",
  "bank_account_masked": "****1234",
  "bank_routing_masked": "****5678",
  "bank_details_changed": true,
  "verdict": "verify",
  "verdict_explanation": "Bank account details differ from the previous request...",
  "recommended_action": "Contact ABC Plumbing LLC directly...",
  "risk_score": 65,
  "prior_check_id": "uuid",
  "decision": "held",
  "decided_by": {
    "id": "uuid",
    "display_name": "Jane Smith"
  },
  "decided_at": "2026-04-04T15:00:00Z",
  "decision_note": "Calling vendor to confirm.",
  "submitted_by": {
    "id": "uuid",
    "display_name": "Jane Smith"
  },
  "signals": [
    {
      "id": "uuid",
      "signal_type": "bank_change_detected",
      "severity": "high",
      "title": "Bank details changed",
      "description": "Account number differs from previous check on 2026-03-15.",
      "metadata": {
        "field": "account_number",
        "previous_masked": "****5678",
        "current_masked": "****1234"
      }
    }
  ],
  "source_file": null,
  "created_at": "2026-04-04T14:30:00Z",
  "updated_at": "2026-04-04T15:00:00Z"
}
```

When a source file exists:
```json
"source_file": {
  "id": "uuid",
  "original_filename": "vendor_bank_change.pdf",
  "mime_type": "application/pdf",
  "file_size_bytes": 45230
}
```

**Success status code:** `200 OK`  
**Error status codes:**
- `401 Unauthorized`
- `403 Forbidden` — Check belongs to a different workspace.
- `404 Not Found` — Check ID does not exist.

**Notes for v1 simplification:** Signals are eagerly loaded (JOIN) — no separate endpoint. `source_file` object is included inline; the actual download URL is obtained via endpoint 12.8. `raw_input_text` IS included in detail (but NOT in list).

---

### 12.7 `POST /api/v1/checks/{check_id}/decision`

**Purpose:** Log a decision on a check. Decisions are **immutable** — this endpoint can only be called once per check.  
**Auth required?** Yes. **Role required:** `admin` or `reviewer` for `approved`. Any role for `held` or `rejected`.

**Request body:**
```json
{
  "decision": "approved",
  "note": "Verified via phone call with vendor."
}
```

**Validation:**
- `decision`: required, one of `approved`, `held`, `rejected`.
- `note`: optional, string, max 500 characters.

**Response body (200):**
```json
{
  "id": "uuid",
  "decision": "approved",
  "decided_by": {
    "id": "uuid",
    "display_name": "Jane Smith"
  },
  "decided_at": "2026-04-04T15:00:00Z",
  "decision_note": "Verified via phone call with vendor."
}
```

**Success status code:** `200 OK`  
**Error status codes:**
- `401 Unauthorized`
- `403 Forbidden` — Member attempting `approved`, or check belongs to a different workspace.
- `404 Not Found` — Check does not exist.
- `409 Conflict` — Check `status` is not `analyzed` (cannot decide on `processing` or `error` checks). Also returned if a decision already exists on this check (`already_decided`).
- `422 Unprocessable Entity` — Invalid decision value or note too long.

**Notes for v1 simplification:** Decisions are **immutable**. Once submitted they cannot be changed. This endpoint returns 409 `already_decided` if a decision is already recorded. Because decisions are immutable, there is no decision audit log table in v1. If a team member needs to change a decision, they submit a new check.

---

### 12.8 `GET /api/v1/checks/{check_id}/file`

**Purpose:** Get a time-limited signed URL to download the source PDF.  
**Auth required?** Yes.

**Request body:** None.

**Response body (200):**
```json
{
  "download_url": "https://xxx.supabase.co/storage/v1/object/sign/check-files/...",
  "expires_in_seconds": 300,
  "original_filename": "vendor_bank_change.pdf"
}
```

**Success status code:** `200 OK`  
**Error status codes:**
- `401 Unauthorized`
- `403 Forbidden` — Check belongs to different workspace.
- `404 Not Found` — Check has no source file (was paste_text input).

**Notes for v1 simplification:** Generates signed URL via Supabase Storage SDK. URL expires in 5 minutes. Frontend opens the URL in a new tab or iframe.

---

## 13. Validation Rules

### Global rules
- All string fields are trimmed of leading/trailing whitespace before processing.
- UUIDs are validated as v4 format.
- Timestamps in responses are ISO 8601 with UTC timezone (`Z` suffix).
- JWT must be present in `Authorization: Bearer <token>` header for all endpoints.

### Per-endpoint rules

| Endpoint | Field | Rule |
|----------|-------|------|
| POST /members | `email` | Required. Valid email format (RFC 5322 basic). |
| POST /members | `role` | Required. One of: `reviewer`, `member`. |
| POST /checks | `input_type` | Required. One of: `paste_text`, `pdf`. |
| POST /checks | `raw_text` | Required if `input_type=paste_text`. 1–50,000 chars. |
| POST /checks | `file` | Required if `input_type=pdf`. Must be `application/pdf`. Max 5MB. |
| POST /decision | `decision` | Required. One of: `approved`, `held`, `rejected`. |
| POST /decision | `note` | Optional. Max 500 chars. |
| GET /checks | `page` | Optional. Integer ≥ 1. |
| GET /checks | `per_page` | Optional. Integer 1–100. |
| GET /checks | `verdict` | Optional. One of: `safe`, `verify`, `blocked`. |
| GET /checks | `decision` | Optional. One of: `approved`, `held`, `rejected`, `pending`. |
| GET /checks | `search` | Optional. 1–100 chars. |

---

## 14. Error Model

### Standard error response shape

Every error response uses this structure:

```json
{
  "error": "error_code",
  "message": "Human-readable description.",
  "details": null
}
```

- `error`: machine-readable snake_case code. Stable across versions.
- `message`: human-readable. May change. Not for programmatic use.
- `details`: nullable object. Used for validation errors only.

### Validation error example (422)

```json
{
  "error": "validation_error",
  "message": "Request body has invalid fields.",
  "details": {
    "fields": [
      { "field": "name", "issue": "required" },
      { "field": "email", "issue": "invalid_format" }
    ]
  }
}
```

### Error code catalog

| HTTP Status | Error Code | When |
|-------------|-----------|------|
| 401 | `unauthorized` | Missing, expired, or invalid JWT |
| 403 | `forbidden` | Valid JWT but insufficient role / wrong workspace |
| 403 | `email_not_verified` | Email verification not completed |
| 404 | `not_found` | Resource does not exist or is in a different workspace |
| 404 | `user_not_found` | Target email has no Supabase Auth account (member addition) |
| 409 | `conflict` | Duplicate (user already a member of this workspace) |
| 409 | `check_not_analyzed` | Trying to decide on a check that isn't in `analyzed` status |
| 409 | `already_decided` | A decision already exists on this check. Decisions are immutable. |
| 413 | `payload_too_large` | File upload exceeds 5MB |
| 415 | `unsupported_media_type` | Uploaded file is not PDF |
| 422 | `validation_error` | Request body fails validation |
| 429 | `workspace_member_limit` | Workspace already has 3 members (beta cap) |
| 500 | `internal_error` | Unexpected server error |
| 503 | `ai_service_unavailable` | OpenAI API timeout or failure |

---

## 15. Recommended Implementation Order

Build sequentially. Each step produces a testable, deployable increment.

### Phase 1: Auth + Context + Core Check Flow

| Step | What | Notes |
|------|------|-------|
| 1.1 | Set up Supabase project (Postgres + Auth + Storage) | Create project, get service role key, configure email verification, create private `check-files` bucket |
| 1.2 | Create database tables: `profiles`, `workspaces`, `workspace_members` | Apply SQL via Supabase dashboard |
| 1.3 | FastAPI project scaffold: JWT verification middleware | Verify Supabase JWT on every request, extract user_id |
| 1.4 | `GET /api/v1/me` — with auto-create workspace logic | On first call for a verified user: create workspace + admin membership atomically. Return full user + workspace context. |
| 1.5 | Create database tables: `check_requests`, `risk_signals`, `source_files` | |
| 1.6 | `POST /api/v1/checks` — paste_text path only (no AI yet) | Save check_request, return stub verdict to test round-trip |
| 1.7 | Text extraction + field parsing | Extract vendor_name, bank details. Compute hashes + masks. |
| 1.8 | Prior-check comparison logic | Query previous checks for same vendor_name, compare hashes, set `bank_details_changed` and `prior_check_id` |
| 1.9 | OpenAI integration: analysis + verdict + signals | Call OpenAI, parse structured response, insert risk_signals, set verdict |
| 1.10 | `POST /api/v1/checks` — PDF path | Upload to Supabase Storage, extract text via pdfplumber, then same pipeline |
| 1.11 | `GET /api/v1/checks` — inbox listing | Paginated list with verdict/status/decision/search filters |
| 1.12 | `GET /api/v1/checks/{check_id}` — detail | Full detail including signals array and source_file |
| 1.13 | `GET /api/v1/checks/{check_id}/file` — signed URL | Generate Supabase Storage signed URL |

**Milestone:** Signup → verify email → auto-workspace created → submit pasted text or PDF → see AI verdict + signals → browse inbox.

### Phase 2: Decisions + Team + Polish

| Step | What | Notes |
|------|------|-------|
| 2.1 | `POST /api/v1/checks/{check_id}/decision` | Immutable decision with role-based permission enforcement |
| 2.2 | Decision filtering in inbox (`?decision=pending`) | Filter by decision status |
| 2.3 | `GET /api/v1/workspaces/{id}/members` | Read-only member list |
| 2.4 | `POST /api/v1/workspaces/{id}/members` | Admin adds teammate by email |
| 2.5 | Error handling pass | Validate all error codes, edge cases, missing extraction data |
| 2.6 | Rate limiting (basic) | Per-user request throttle to protect OpenAI budget |

**Milestone:** Full v1 backend is functional and API-testable. Decisions logged. Team access working.

---

## 16. Final Locked Recommendation

### Architecture

- **6 tables** for launch. No more.
- **8 endpoints**. No more.
- **Workspace auto-created** via `GET /api/v1/me` on first authenticated call — no separate creation endpoint.
- **Decisions are immutable.** One decision per check, no update path. No decision audit log needed.
- **Member management (add only)** deferred to Phase 2. PATCH role and DELETE member handled via Supabase dashboard for the beta period.
- **Synchronous processing** for check submission. No background workers, no queues, no polling.
- **Application-level authorization** in FastAPI. No Postgres RLS in v1 (add later as hardening).
- **Single workspace per user** enforced at application level.
- **3-member cap** per workspace, hardcoded.
- **No vendors table** in v1. Vendor identity is derived from `check_requests.vendor_name`.

### Key design choices and why

| Choice | Alternatives Considered | Why This One |
|--------|------------------------|-------------|
| Decision fields on check_requests, immutable once set | Mutable decision with audit log | One query gets the full check state. Immutability removes the audit table entirely. If a decision must change, a new check is submitted. |
| Auto-create workspace on first `GET /me` | POST /workspaces onboarding step | Removes an API call from the onboarding flow. Workspace is always ready when the user lands in the app. |
| risk_signals as separate rows (not JSON on check_requests) | JSONB column | Signals need structured filtering, counting, and display. Separate rows enable this without parsing JSON. |
| JSONB metadata on risk_signals | Additional typed columns per signal type | Signal types will evolve. JSONB avoids migrations for new signal shapes. Only one JSONB column in the entire schema. |
| Synchronous POST /checks | Async with polling / webhooks / realtime | 3 users, no concurrency pressure. Sync is dramatically simpler to build, test, and debug. |
| Workspace scoped via JWT (not URL path) | /workspaces/{id}/checks/{id} | Prevents IDOR. Removes workspace_id from every frontend URL. Simpler routing. |
| Multipart/form-data for check submission | Separate upload endpoint + JSON create | Single API call for both text and PDF. Simpler frontend integration. |
| SHA-256 without salt for bank detail comparison | bcrypt, HMAC, salted hash | These are comparison hashes, not password hashes. Same-value comparison requires deterministic output. Never exposed via API. |

### What NOT to build

- Do not build `POST /workspaces`. Workspace is auto-created.
- Do not build `DELETE /members` or `PATCH /members` endpoints. Use Supabase dashboard for the beta.
- Do not build a decision update/override path. Decisions are immutable. User submits a new check.
- Do not build a workspace_invites table or pending-invite flow. Invitee must sign up first.
- Do not build a vendors CRUD. Derive vendor context from check history.
- Do not build notifications. Users refresh the inbox.
- Do not build analytics. Postgres queries cover beta needs.
- Do not build retry logic for failed checks. User resubmits.
- Do not build file versioning. One file per check, immutable.
- Do not build soft deletes. Hard delete is fine for beta.
- Do not build an admin dashboard. Supabase dashboard covers it.

---

## 17. Blocking Questions

None. All required decisions have been locked. Implementation can proceed.

Non-blocking notes for awareness:
- **OpenAI prompt design** (what prompt extracts fields + evaluates risk) is an implementation detail to resolve during Phase 2, step 2.5. Does not affect the schema or API contract.
- **Supabase Storage bucket ACL configuration** (private bucket, service-role-only access) should be set during Phase 1.1 setup. Does not affect the schema.
- **PDF text extraction library choice** (pdfplumber vs PyPDF2 vs pymupdf) is an implementation detail. Does not affect the contract.

---

*End of specification.*
