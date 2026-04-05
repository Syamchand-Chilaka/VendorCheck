# VendorCheck v1 — Implementation Plan

**Status:** Final build plan — pre-implementation  
**Date:** 2026-04-04  
**Prerequisite:** [v1-schema-and-api-contract.md](v1-schema-and-api-contract.md) (locked)

---

## 1. Known Facts Used

- Monorepo already exists at `/VendorCheck` with `apps/web` (Next.js 16, Tailwind v4) and `apps/api` (FastAPI, empty)
- Landing page is built and deployed via GitHub Pages
- Backend `main.py` is empty. No `requirements.txt` or `pyproject.toml` exists yet. A `.venv/` directory is present.
- 6 launch tables, 8 launch endpoints defined in the API contract
- Locked tech: Supabase Postgres + Storage + Auth, FastAPI, Next.js, OpenAI
- Locked constraints: synchronous check processing, immutable decisions, no vendors table, workspace auto-created on first `/me` call, 3-member cap
- `next.config.ts` currently uses `output: "export"` for GitHub Pages static export — this must change to support dynamic app routes while preserving the landing page deployment

---

## 2. Explicit Assumptions

| # | Assumption | Rationale |
|---|-----------|-----------|
| P1 | The landing page stays deployed on GitHub Pages via static export. The actual app (authenticated routes) will be deployed separately (e.g., Vercel free tier) with server-side rendering. | Static export cannot handle auth callbacks, middleware, or API proxying. Two deployment targets from one Next.js app using build-time config. |
| P2 | FastAPI will be deployed on Railway free tier or Render free tier. | Cheapest option within the $20–30/month budget. Provides always-on hosting with easy env var config. |
| P3 | The frontend talks to the FastAPI backend directly (CORS configured). No BFF pattern. | Simplest architecture for solo founder. The JWT from Supabase Auth is sent directly to FastAPI. |
| P4 | Supabase JS SDK is used on the frontend for auth only (signup, login, email verification, session tokens). All data operations go through FastAPI. | Clear separation: Supabase handles auth UX, FastAPI handles all business logic and data access. |
| P5 | No shared TypeScript/Python type generation tool in v1. API types are manually kept in sync between the contract doc, FastAPI Pydantic models, and frontend TypeScript types. | Adding openapi-typescript or similar adds toolchain complexity. With 8 endpoints the manual sync cost is low. |
| P6 | `next.config.ts` will be reconfigured: remove `output: "export"` for the app deployment. The GitHub Pages deploy workflow will use a separate build command with the export flag. | Allows both static landing page export and dynamic app rendering from the same codebase. |

---

## 3. Repo Strategy Decision

**Decision: Keep the existing monorepo.**

Reasons:
- Already in place (`apps/web`, `apps/api`, `docs/`)
- Solo founder: one `git push` deploys context for everything
- Shared docs live alongside code
- No cross-app package sharing needed — no `packages/` folder required
- Separate repos add git overhead with zero benefit at this scale

No changes to the top-level repo structure.

---

## 4. Final Folder Structure

```
VendorCheck/
├── .github/
│   └── workflows/
│       └── deploy.yml              # GitHub Pages (landing page only)
├── .gitignore
├── README.md
├── docs/
│   ├── v1-schema-and-api-contract.md
│   └── v1-implementation-plan.md   # this file
├── apps/
│   ├── api/
│   │   ├── .venv/                  # local virtualenv (gitignored)
│   │   ├── pyproject.toml          # dependencies + project metadata
│   │   ├── .env                    # local env vars (gitignored)
│   │   ├── .env.example            # checked-in template
│   │   ├── alembic.ini             # (defer) DB migrations — use Supabase SQL editor for v1
│   │   └── app/
│   │       ├── __init__.py
│   │       ├── main.py             # FastAPI app, CORS, lifespan, router mount
│   │       ├── config.py           # settings from env vars (pydantic-settings)
│   │       ├── deps.py             # shared dependencies: get_current_user, get_db, get_supabase
│   │       ├── auth.py             # JWT verification, user context extraction
│   │       ├── errors.py           # error model, exception handlers
│   │       ├── models/
│   │       │   ├── __init__.py
│   │       │   └── enums.py        # Role, InputType, CheckStatus, Verdict, Decision, SignalSeverity
│   │       ├── schemas/
│   │       │   ├── __init__.py
│   │       │   ├── me.py           # MeResponse
│   │       │   ├── members.py      # MemberResponse, AddMemberRequest
│   │       │   ├── checks.py       # CreateCheckResponse, CheckListResponse, CheckDetailResponse
│   │       │   ├── decisions.py    # DecisionRequest, DecisionResponse
│   │       │   └── files.py        # FileUrlResponse
│   │       ├── routes/
│   │       │   ├── __init__.py
│   │       │   ├── me.py           # GET /api/v1/me
│   │       │   ├── members.py      # GET + POST /api/v1/workspaces/{id}/members
│   │       │   ├── checks.py       # POST + GET list + GET detail
│   │       │   ├── decisions.py    # POST /api/v1/checks/{id}/decision
│   │       │   └── files.py        # GET /api/v1/checks/{id}/file
│   │       ├── services/
│   │       │   ├── __init__.py
│   │       │   ├── workspace.py    # auto-create workspace, member operations
│   │       │   ├── checks.py       # create check, list, detail, prior-check comparison
│   │       │   ├── analysis.py     # extraction + OpenAI analysis + signal generation
│   │       │   ├── decisions.py    # log decision with permission check
│   │       │   └── storage.py      # Supabase Storage upload + signed URL
│   │       └── db/
│   │           ├── __init__.py
│   │           └── queries.py      # raw SQL queries via supabase-py or asyncpg
│   └── web/
│       ├── package.json
│       ├── next.config.ts
│       ├── tsconfig.json
│       ├── postcss.config.mjs
│       ├── eslint.config.mjs
│       ├── .env.local              # local env vars (gitignored)
│       ├── .env.example            # checked-in template
│       ├── app/
│       │   ├── globals.css
│       │   ├── layout.tsx          # root layout (landing page)
│       │   ├── page.tsx            # landing page (existing)
│       │   ├── components/         # landing page components (existing)
│       │   │   ├── Header.tsx
│       │   │   ├── Hero.tsx
│       │   │   ├── ... (existing)
│       │   ├── (auth)/
│       │   │   ├── layout.tsx      # minimal auth layout (no sidebar)
│       │   │   ├── login/
│       │   │   │   └── page.tsx
│       │   │   ├── signup/
│       │   │   │   └── page.tsx
│       │   │   └── verify/
│       │   │       └── page.tsx    # email verification waiting/callback
│       │   └── (dashboard)/
│       │       ├── layout.tsx      # authenticated layout: sidebar + header
│       │       ├── inbox/
│       │       │   └── page.tsx    # check list / inbox
│       │       ├── checks/
│       │       │   ├── new/
│       │       │   │   └── page.tsx    # new check submission form
│       │       │   └── [id]/
│       │       │       └── page.tsx    # check detail + decision
│       │       └── members/
│       │           └── page.tsx    # workspace member list + add
│       ├── lib/
│       │   ├── supabase.ts         # Supabase client (browser) for auth only
│       │   ├── api.ts              # fetch wrapper for FastAPI calls
│       │   └── types.ts            # API response types (manual, matches Pydantic schemas)
│       ├── hooks/
│       │   ├── use-auth.ts         # auth state, session, redirect
│       │   └── use-api.ts          # thin data-fetching hook (fetch + loading + error)
│       └── components/
│           ├── ui/                  # shared UI primitives
│           │   ├── Button.tsx
│           │   ├── Input.tsx
│           │   ├── Badge.tsx
│           │   ├── Card.tsx
│           │   └── Spinner.tsx
│           ├── AuthGuard.tsx        # redirects unauthenticated users
│           ├── VerdictBadge.tsx     # Safe / Verify / Blocked pill
│           ├── SignalCard.tsx       # individual risk signal display
│           └── DecisionForm.tsx     # Approve / Hold / Reject selector + note
```

---

## 5. Backend Structure

### Layer responsibilities

| Layer | What it does | Files |
|-------|-------------|-------|
| **Routes** | HTTP handler. Parse request, call service, return response. No business logic. | `routes/*.py` |
| **Schemas** | Pydantic models for request/response validation. | `schemas/*.py` |
| **Services** | Business logic: orchestrate DB queries, call AI, enforce rules, compute hashes. | `services/*.py` |
| **DB** | Raw SQL queries. No ORM in v1 — use `supabase-py` client or `asyncpg` directly. | `db/queries.py` |
| **Auth** | JWT verification, extract user_id, load workspace context. | `auth.py`, `deps.py` |
| **Config** | Env var loading via pydantic-settings. | `config.py` |
| **Errors** | Centralized error codes and exception handlers. | `errors.py` |

### Key backend decisions

- **No ORM.** Use `supabase-py` (the official Python client) for DB queries via its PostgREST interface. Falls back to raw SQL for complex queries (joins, aggregations). Avoids SQLAlchemy boilerplate and migration tooling.
- **No Alembic in v1.** Schema is applied via the Supabase SQL editor / dashboard. With 6 tables and a solo founder, migration tooling adds complexity without value yet.
- **`supabase-py` for everything Supabase:** Postgres queries, Storage uploads, Storage signed URLs, Auth admin API (for looking up users by email). Single client initialized in `deps.py`.
- **Dependency injection for auth context.** A `get_current_user` dependency verifies the JWT, loads the user's workspace membership, and makes `user_id`, `workspace_id`, and `role` available to every route handler.

### Python dependencies (pyproject.toml)

```
# Core
fastapi
uvicorn[standard]
pydantic-settings
supabase               # official supabase-py client
python-multipart       # for file uploads
pdfplumber             # PDF text extraction
openai                 # OpenAI Python SDK
httpx                  # async HTTP client (used by supabase-py)

# Dev
pytest
pytest-asyncio
ruff                   # linting + formatting
```

---

## 6. Frontend Structure

### Route map

| Route | Auth? | Purpose |
|-------|-------|---------|
| `/` | No | Landing page (existing) |
| `/login` | No | Login form |
| `/signup` | No | Signup form |
| `/verify` | No | Email verification waiting screen |
| `/inbox` | Yes | Check list (main dashboard) |
| `/checks/new` | Yes | Submit new check (paste or PDF) |
| `/checks/[id]` | Yes | Check detail + verdict + signals + decision |
| `/members` | Yes | Workspace member list + add member |

### Key frontend decisions

- **Supabase JS SDK for auth only.** `@supabase/supabase-js` handles signup, login, email verification callbacks, and session token management. All data fetches go through FastAPI via `lib/api.ts`.
- **No global state library.** React state + context is sufficient for 4 authenticated screens. Auth state lives in a context provider wrapping the `(dashboard)` layout.
- **Route groups.** `(auth)` group for unauthenticated flows. `(dashboard)` group for authenticated flows with the shared sidebar layout and `AuthGuard`.
- **`lib/api.ts` is a thin fetch wrapper.** It attaches the Supabase JWT to every request, handles error response parsing, and returns typed data. Not a full SDK — just `get()`, `post()`, `upload()`.
- **`output: "export"` must be removed from next.config.ts** for the app deployment. Route groups with layouts, dynamic `[id]` routes, and middleware require server rendering. The GitHub Pages workflow will pass a build flag to re-enable export for the landing page only.
- **Form validation with native HTML + minimal JS.** No form library. The 2 forms (new check, decision) are simple enough for controlled components with inline validation.
- **`next.config.ts` rewrites for API proxying (optional).** If CORS becomes painful, add a `rewrites` rule to proxy `/api/*` to the FastAPI server. Otherwise, direct fetch with CORS headers is fine.

### Frontend dependencies to add

```
@supabase/supabase-js    # auth only
```

No additional UI library. Tailwind v4 (already installed) covers all styling.

---

## 7. Shared Contracts/Types Strategy

**No automated type sharing in v1.**

- The API contract document is the source of truth.
- FastAPI Pydantic schemas (`app/schemas/*.py`) define the server-side contract.
- Frontend TypeScript types (`lib/types.ts`) mirror those schemas manually.
- With 8 endpoints, the sync burden is ~30 minutes of maintenance total.

**When to upgrade:** If endpoints grow past ~15, add `openapi-typescript` to auto-generate `types.ts` from the FastAPI OpenAPI spec. Not before.

---

## 8. Supabase Setup Checklist

Execute these in order via the Supabase dashboard:

| # | Task | Notes |
|---|------|-------|
| 1 | Create a new Supabase project | Free tier. Region: closest to target users (US East). |
| 2 | Copy project credentials | `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET` |
| 3 | Enable email auth | Settings → Auth → Email provider ON. Enable email confirmation. |
| 4 | Disable other auth providers | Turn off Google, GitHub, etc. Email/password only for v1. |
| 5 | Set redirect URLs | Add `http://localhost:3000/verify` and the production app URL. |
| 6 | Create `check-files` storage bucket | Private bucket. No public access. |
| 7 | Run table creation SQL — profiles | See schema doc §6.1 |
| 8 | Run table creation SQL — workspaces | See schema doc §6.2 |
| 9 | Run table creation SQL — workspace_members | See schema doc §6.3. Add unique constraint + index. |
| 10 | Run table creation SQL — check_requests | See schema doc §6.4. Add all indexes. |
| 11 | Run table creation SQL — risk_signals | See schema doc §6.5 |
| 12 | Run table creation SQL — source_files | See schema doc §6.6. Add unique constraint on check_request_id. |
| 13 | Verify all tables in Table Editor | Confirm columns, types, constraints. |
| 14 | Test auth flow manually | Sign up → receive email → verify → confirm in auth.users. |

---

## 9. Environment Variables

### Backend (`apps/api/.env`)

Never commit a real `SUPABASE_SERVICE_ROLE_KEY`. If one is ever pushed, rotate it immediately in Supabase and purge it from git history.

```
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<service-role-key-set-locally-only>
SUPABASE_JWT_SECRET=<jwt-secret-set-locally-only>
OPENAI_API_KEY=sk-...
ALLOWED_ORIGINS=http://localhost:3000
APP_ENV=development
```

| Variable | Required | Notes |
|----------|----------|-------|
| `SUPABASE_URL` | Yes | Project URL from Supabase dashboard |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | Service role key — NOT the anon key. Gives full DB access. |
| `SUPABASE_JWT_SECRET` | Yes | For JWT verification. Found under Settings → API → JWT Secret. |
| `OPENAI_API_KEY` | Yes | OpenAI API key. |
| `ALLOWED_ORIGINS` | Yes | CORS allowed origins. Comma-separated for production. |
| `APP_ENV` | No | `development` or `production`. Controls debug logging. |

### Frontend (`apps/web/.env.local`)

```
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon-key>
NEXT_PUBLIC_API_URL=http://localhost:8000
```

| Variable | Required | Notes |
|----------|----------|-------|
| `NEXT_PUBLIC_SUPABASE_URL` | Yes | Same Supabase project URL. |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Yes | The **anon** key (safe for browser). Used by Supabase JS SDK for auth. |
| `NEXT_PUBLIC_API_URL` | Yes | FastAPI backend URL. `http://localhost:8000` locally, production URL when deployed. |

### `.env.example` files

Both apps get a `.env.example` checked into git with placeholder values and comments. The actual `.env` / `.env.local` files remain gitignored.

---

## 10. Local Setup Order

Run these once to get a working local dev environment:

| # | Step | Command / Action |
|---|------|-----------------|
| 1 | Clone repo | `git clone https://github.com/Syamchand-Chilaka/VendorCheck.git` |
| 2 | Set up Supabase project | See §8 checklist |
| 3 | Create backend env file | Copy `apps/api/.env.example` to `apps/api/.env`, fill in real values |
| 4 | Create frontend env file | Copy `apps/web/.env.example` to `apps/web/.env.local`, fill in real values |
| 5 | Set up Python virtualenv | `cd apps/api && python3 -m venv .venv && source .venv/bin/activate` |
| 6 | Install Python deps | `pip install -e ".[dev]"` (once pyproject.toml exists) |
| 7 | Start backend | `cd apps/api && uvicorn app.main:app --reload --port 8000` |
| 8 | Install frontend deps | `cd apps/web && npm install` |
| 9 | Start frontend | `cd apps/web && npm run dev` |
| 10 | Verify | Open `http://localhost:3000`, sign up, check `/api/v1/me` returns 200 |

---

## 11. Implementation Phases

### Phase 1: Backend Core (auth + check submission + analysis)

**Goal:** A working API that accepts a check, runs AI analysis, and returns results. Testable via curl / Postman.

Steps: Supabase setup → FastAPI scaffold → JWT auth → `GET /me` with auto-workspace → `POST /checks` (paste text) → extraction + hashing → prior-check comparison → OpenAI integration → `POST /checks` (PDF) → `GET /checks` (list) → `GET /checks/{id}` (detail) → `GET /checks/{id}/file` (signed URL)

### Phase 2: Backend Complete (decisions + team + hardening)

**Goal:** All 8 endpoints working. Decision logging. Member management. Error handling solid.

Steps: `POST /checks/{id}/decision` → decision filtering in inbox → `GET /members` → `POST /members` → error handling pass → basic rate limiting

### Phase 3: Frontend Auth + Core Screens

**Goal:** Users can sign up, submit checks, and see results in the browser.

Steps: Supabase JS auth setup → login/signup/verify screens → AuthGuard + dashboard layout → inbox page → new check form → check detail page

### Phase 4: Frontend Complete + Polish

**Goal:** Full v1 frontend. Members page. Decision UI. Error states. Responsive polish.

Steps: Decision form on check detail → member list/add page → loading/error states → responsive pass → final integration testing

---

## 12. API Implementation Order

Build each endpoint fully (route → schema → service → DB query → test) before moving to the next.

| # | Endpoint | Dependencies | Notes |
|---|----------|-------------|-------|
| 1 | `GET /api/v1/me` | JWT auth middleware, Supabase client | First endpoint. Auto-creates workspace. |
| 2 | `POST /api/v1/checks` (paste_text) | Check creation service, extraction logic | Stub AI first (return dummy verdict), then wire OpenAI. |
| 3 | `POST /api/v1/checks` (pdf) | Storage upload, pdfplumber extraction | Extends #2 with file handling. |
| 4 | `GET /api/v1/checks` | List query with filters + pagination | |
| 5 | `GET /api/v1/checks/{id}` | Detail query with signals JOIN | |
| 6 | `GET /api/v1/checks/{id}/file` | Supabase Storage signed URL | |
| 7 | `POST /api/v1/checks/{id}/decision` | Permission check (role-based), immutability enforcement | |
| 8 | `GET /api/v1/workspaces/{id}/members` | Supabase Auth admin API for email lookup | |
| 9 | `POST /api/v1/workspaces/{id}/members` | User lookup by email, membership creation | |

---

## 13. Frontend Implementation Order

| # | Screen | Dependencies | Notes |
|---|--------|-------------|-------|
| 1 | Supabase auth config + `lib/supabase.ts` | Supabase project exists | |
| 2 | `lib/api.ts` + `lib/types.ts` | | Fetch wrapper + types for all 8 endpoints |
| 3 | Login page | Supabase signInWithPassword | |
| 4 | Signup page | Supabase signUp | |
| 5 | Email verification page | Supabase onAuthStateChange | |
| 6 | `use-auth` hook + `AuthGuard` | | Session management, redirect logic |
| 7 | Dashboard layout (sidebar + header) | AuthGuard, `GET /me` | |
| 8 | Inbox page | `GET /checks` | List with verdict badges, pagination, filters |
| 9 | New Check page | `POST /checks` | Paste text tab + PDF upload tab. Loading spinner during analysis. |
| 10 | Check Detail page | `GET /checks/{id}` | Verdict, signals, source file link, decision form |
| 11 | Decision form | `POST /checks/{id}/decision` | Approve/Hold/Reject with note. Shows existing decision if set. |
| 12 | Members page | `GET /members`, `POST /members` | Simple list + add-by-email form |

---

## 14. Data Flow Overview

### Check submission (paste text)

```
Frontend                          FastAPI                           Supabase / OpenAI
─────────                         ───────                           ─────────────────
POST /checks                 →    Validate input_type + raw_text
(multipart/form-data)             Extract fields from text
                                  Compute bank_account_hash, bank_routing_hash
                                  Compute bank_account_masked, bank_routing_masked
                                  Query prior check (same vendor_name, same workspace)
                                  Compare hashes → set bank_details_changed
                                  Insert check_requests row (status=processing)  →  Postgres INSERT
                                  Call OpenAI with structured prompt              →  OpenAI API
                                  Parse response → verdict, explanation, signals
                                  Insert risk_signals rows                        →  Postgres INSERT
                                  Update check_requests (status=analyzed, verdict) → Postgres UPDATE
                             ←    Return full check + signals (201)
```

### Check submission (PDF)

```
Frontend                          FastAPI                           Supabase
─────────                         ───────                           ────────
POST /checks                 →    Validate input_type + file
(multipart/form-data)             Upload file to Supabase Storage                →  Storage PUT
                                  Insert source_files row                        →  Postgres INSERT
                                  Extract text from PDF via pdfplumber
                                  (same pipeline as paste_text from here)
                             ←    Return full check + signals (201)
```

### Decision logging

```
Frontend                          FastAPI                           Supabase
─────────                         ───────                           ────────
POST /checks/{id}/decision   →    Verify workspace ownership
                                  Verify check status = analyzed
                                  Verify decision is null (immutability)
                                  Verify role permission (approve requires admin/reviewer)
                                  Update check_requests (decision, decided_by, decided_at) → Postgres UPDATE
                             ←    Return decision summary (200)
```

---

## 15. Testing Strategy

Realistic for a solo founder. No 100% coverage target.

### Priority tiers

| Tier | What | How | When |
|------|------|-----|------|
| **P0 — Must have** | JWT auth middleware | pytest — valid token, expired token, missing token, wrong workspace | Before any endpoint ships |
| **P0 — Must have** | `POST /checks` happy path | pytest — paste_text input, verify DB rows created, response shape matches schema | After check creation works |
| **P0 — Must have** | Decision immutability | pytest — decide once succeeds, decide twice returns 409 | After decision endpoint works |
| **P1 — Should have** | Role permissions | pytest — member cannot approve, reviewer can | After decision + member endpoints work |
| **P1 — Should have** | Hash comparison logic | pytest unit test — same input = same hash, different input = different hash | After extraction logic works |
| **P1 — Should have** | PDF extraction | pytest — upload a test PDF, verify extracted text | After PDF path works |
| **P2 — Nice to have** | End-to-end via browser | Manual test script: signup → submit check → see result → decide | Before beta launch |
| **P2 — Nice to have** | OpenAI mock | pytest — mock OpenAI response, verify signal insertion | Useful for CI, not blocking |

### Test tools

- `pytest` + `pytest-asyncio` for backend
- No frontend testing framework in v1 — manual testing is sufficient for 4 screens
- Use a dedicated Supabase test project (or the same project with test data cleanup)

### Test file location

```
apps/api/tests/
├── conftest.py           # fixtures: test client, auth headers, test user
├── test_auth.py          # JWT verification
├── test_checks.py        # check creation, listing, detail
├── test_decisions.py     # decision logging + immutability
└── test_extraction.py    # hash computation, field parsing
```

---

## 16. Dev Seed Data Strategy

**No automated seed script in v1.** Manual seeding is fine for ≤3 users.

### Manual setup for development

1. Sign up via the app (creates auth.users + profiles + workspaces + workspace_members automatically)
2. Submit 3–5 checks via the New Check form with varied text:
   - A clean vendor bank-change request (should be Safe)
   - A suspicious request with urgency language (should be Verify or Blocked)
   - A request from the same vendor with different bank details (should trigger `bank_details_changed`)
   - A PDF upload
3. Log decisions on some checks (leave others pending for testing the pending filter)

### Sample paste text for testing

Keep 3–4 sample vendor request texts in `docs/test-data/` (not checked into production, or ignored). These are input strings to paste during development.

---

## 17. Deployment Plan

### Landing page (already deployed)

- GitHub Pages via `.github/workflows/deploy.yml`
- Static export of the Next.js app (current setup)
- No changes needed

### FastAPI backend

| Item | Choice | Notes |
|------|--------|-------|
| Platform | **Render** (free tier) or **Railway** ($5/month hobby) | Both support Python, env vars, auto-deploy from GitHub |
| Deploy trigger | Push to `main` branch, filtered to `apps/api/**` | |
| Build command | `pip install -r requirements.txt` (or `pip install .`) | |
| Start command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` | |
| Root directory | `apps/api` | |
| Environment | Set all vars from §9 | |
| Custom domain | `api.vendorcheck.app` or subdomain (later) — use platform default URL for beta | |

### Next.js app (authenticated routes)

| Item | Choice | Notes |
|------|--------|-------|
| Platform | **Vercel** (free tier) | Best Next.js support. Auto-detects framework. Free for personal projects. |
| Deploy trigger | Push to `main` branch, filtered to `apps/web/**` | |
| Root directory | `apps/web` | |
| Build settings | Remove `output: "export"` for app deployment. Vercel handles SSR. | |
| Environment | Set all `NEXT_PUBLIC_*` vars from §9 | |
| Custom domain | `app.vendorcheck.app` (later) — use Vercel default URL for beta | |

### Deployment order

1. Deploy FastAPI to Render/Railway first (get the API URL)
2. Set `NEXT_PUBLIC_API_URL` on Vercel to the FastAPI URL
3. Deploy Next.js app to Vercel
4. Test end-to-end: signup → check → decision

---

## 18. Monitoring and Error Handling

### v1 approach (minimal, free)

| Concern | Solution | Notes |
|---------|----------|-------|
| Backend errors | Python `logging` to stdout. Render/Railway capture logs automatically. | No external error tracker in v1. |
| Unhandled exceptions | FastAPI exception handler in `errors.py` — catches all, returns 500 with `internal_error` code. Logs full traceback. | |
| OpenAI failures | Catch `openai.APIError` and `openai.APITimeoutError`. Save check with `status=error`. Return 201 with error data. | User sees the error in the UI and can resubmit. |
| Frontend errors | Browser console + React error boundary on the dashboard layout. | No Sentry in v1. |
| Uptime | Render/Railway provide basic health checks. Add a `GET /health` endpoint that returns 200. | |
| OpenAI budget tracking | Log token usage from each API response. Check the OpenAI dashboard weekly. | No programmatic budget enforcement in v1. |

### Upgrade path

Add Sentry (free tier: 5,000 events/month) if errors become hard to reproduce after beta launch. Not needed for first 3 users.

---

## 19. First 10 Build Tasks

Execute in this exact order. Each task is self-contained and testable.

| # | Task | Output |
|---|------|--------|
| 1 | **Create Supabase project, configure auth + storage** | Supabase project live. Email auth enabled. `check-files` bucket created. Credentials copied to `.env` files. |
| 2 | **Create all 6 database tables via Supabase SQL editor** | All tables, constraints, indexes visible in Supabase Table Editor. |
| 3 | **Scaffold FastAPI project: pyproject.toml, app structure, config, health endpoint** | `uvicorn app.main:app --reload` starts. `GET /health` returns 200. |
| 4 | **Implement JWT auth middleware + `GET /api/v1/me` with auto-workspace** | Sign up via Supabase dashboard → call `/me` with JWT → get user + workspace back. Workspace auto-created. |
| 5 | **Implement `POST /api/v1/checks` (paste_text, stub AI)** | Post pasted text → get back a check with `status=analyzed` and a dummy verdict. Row exists in `check_requests`. |
| 6 | **Implement text extraction + hash/mask computation** | Extraction service parses vendor_name, bank details from text. Hashes and masks are computed and stored. |
| 7 | **Implement OpenAI integration: analysis + verdict + signals** | Post pasted text → get back real AI verdict + risk signals. Rows exist in `risk_signals`. |
| 8 | **Implement `POST /api/v1/checks` (PDF path)** | Upload a PDF → file stored in Supabase Storage → text extracted → same analysis pipeline → source_files row created. |
| 9 | **Implement `GET /api/v1/checks` (list) + `GET /api/v1/checks/{id}` (detail) + `GET /checks/{id}/file`** | Inbox listing with filters. Detail with signals. Signed URL for PDF download. |
| 10 | **Implement `POST /api/v1/checks/{id}/decision` with immutability + role check** | Log a decision → stored on check row. Second attempt → 409. Member trying approve → 403. |

**After task 10:** The entire backend API is functional. Begin frontend implementation (Phase 3).

---

## 20. Deferred Items

Explicitly NOT in the v1 build plan:

| Item | Why Deferred | When to Revisit |
|------|-------------|----------------|
| Database migrations (Alembic) | SQL editor is sufficient for 6 tables. Migrations add toolchain complexity. | When schema changes become frequent (v2+). |
| Automated type generation (openapi-typescript) | 8 endpoints. Manual sync is faster than toolchain setup. | When endpoints exceed ~15. |
| Frontend unit/integration tests | 4 screens, solo founder, manual testing is faster. | When a second developer joins or regressions appear. |
| Seed data script | ≤3 beta users. Manual seeding takes 5 minutes. | When onboarding new developers or running CI. |
| Sentry / error monitoring | 3 users, low traffic, logs are sufficient. | After beta launch if errors are hard to reproduce. |
| CI/CD pipeline (GitHub Actions for tests) | Manual local testing is sufficient for solo founder. | When automated deploy gates are needed. |
| Custom domains | Platform default URLs work for beta. | When marketing or customer-facing branding matters. |
| `vendors` table | Vendor identity derived from `vendor_name` on checks. | When vendor profiles, settings, or cross-workspace data are needed. |
| `workspace_invites` table | Admin adds users by email (must already have account). | When pending-invite UX is required. |
| `decision_audit_log` table | Decisions are immutable. No log needed. | When mutable decisions or compliance features are scoped. |
| PATCH/DELETE member endpoints | Admin manages via Supabase dashboard for beta. | When team management is a user-facing product feature. |
| Rate limiting | ≤3 users. OpenAI budget tracked manually. | When public access or abuse risk increases. |
| Background job processing | Synchronous check analysis is acceptable for ≤3 users. | When response times become unacceptable or concurrent users increase. |

---

## 21. Risks and Mitigations

| # | Risk | Impact | Mitigation |
|---|------|--------|-----------|
| 1 | OpenAI response time > 15 seconds | Poor UX — user thinks the app is broken | Frontend shows a prominent loading spinner with "Analyzing... this takes 5–15 seconds" message. Backend has a 30-second timeout on the OpenAI call. If timeout, save check with `status=error`. |
| 2 | OpenAI returns unparseable response | Check saved with no verdict, no signals | Define a strict structured output schema (JSON mode or function calling). Validate the response shape before processing. Fall back to `status=error` with explanation. |
| 3 | PDF text extraction fails (malformed PDF) | Check saved with no extracted fields | Catch pdfplumber exceptions. Save check with `status=error` and `analysis_error` explaining the issue. |
| 4 | Supabase free tier limits hit | DB or storage becomes unavailable | Monitor via Supabase dashboard. Free tier provides 500MB DB + 1GB storage — more than enough for beta. |
| 5 | `next.config.ts` export mode conflicts | Landing page deploy breaks when switching to dynamic rendering | Use environment variable to conditionally set `output: "export"`. GitHub Pages workflow sets the flag; Vercel does not. |
| 6 | JWT verification edge cases | Auth bypass or 401 storms | Test JWT middleware thoroughly (expired, malformed, wrong secret, missing). This is task 4's test target. |
| 7 | Bank detail hashing inconsistency | False negatives in change detection | Normalize input (strip whitespace, remove dashes, lowercase) before hashing. Unit test with edge cases. |
| 8 | CORS misconfiguration | Frontend cannot reach backend | Set `ALLOWED_ORIGINS` explicitly. Test cross-origin requests locally before deploying. |

---

## 22. Final Execution Sequence

The complete build path from current state to beta-ready:

```
Week 1: Backend Foundation
├── Task 1: Supabase project + auth + storage setup
├── Task 2: Create all 6 database tables
├── Task 3: FastAPI scaffold + health endpoint
├── Task 4: JWT auth + GET /me + auto-workspace
└── Task 5: POST /checks (paste_text, stub AI)

Week 2: Backend Intelligence
├── Task 6: Text extraction + hash/mask computation
├── Task 7: OpenAI integration + signals
├── Task 8: POST /checks (PDF path)
├── Task 9: GET /checks (list) + GET /checks/{id} (detail) + file URL
└── Task 10: POST /decision + immutability + permissions

Week 3: Frontend Core
├── Supabase JS auth setup + auth pages (login/signup/verify)
├── AuthGuard + dashboard layout
├── Inbox page (list with filters)
├── New check page (paste text + PDF upload)
└── Check detail page (verdict + signals)

Week 4: Frontend Complete + Launch
├── Decision form on check detail
├── Members page (list + add)
├── Loading/error states across all screens
├── Responsive polish
├── Deploy backend (Render/Railway)
├── Deploy frontend (Vercel)
└── End-to-end smoke test → beta ready
```

**Total: ~4 calendar weeks of focused solo work.**

This is not a prediction — it's a sequencing guide. The order is what matters.

---

*End of implementation plan.*
