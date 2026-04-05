-- ==========================================================================
-- VendorCheck v1 — Consolidated AWS-native PostgreSQL Schema
-- Migration: 003_v1_consolidated.sql
-- Target:    Amazon RDS PostgreSQL 16
-- Purpose:   Canonical single-file schema for VendorCheck MVP.
--            Supersedes 001_init.sql + 002_rls.sql (kept for history).
-- ==========================================================================
-- IMPORTANT: This file is designed for FRESH DATABASE SETUP only.
-- It is NOT a safe incremental migration for an existing 001+002 database.
--
-- Reason: Enum types are created via `DO $$ EXCEPTION WHEN duplicate_object`
-- which silently skips the block if the type already exists. New enum values
-- (e.g. workflow_status, contributor, viewer) will NOT be applied to an
-- existing database. To upgrade 001+002 in-place, write a dedicated
-- 004_role_upgrade.sql that uses ALTER TYPE ... ADD VALUE / RENAME VALUE.
--
-- Safe table DDL (IF NOT EXISTS), index DDL (IF NOT EXISTS), ALTER TABLE
-- deferred FKs, and RLS policy drops+recreates ARE idempotent and safe
-- to re-run after initial setup.
-- ==========================================================================

BEGIN;

-- ── Extensions ───────────────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── Enum types ───────────────────────────────────────────────────────────
-- Drop-if-exists pattern: safe for fresh DB, skip on upgrade.

DO $$ BEGIN
  CREATE TYPE user_role AS ENUM ('owner', 'admin', 'reviewer', 'contributor', 'viewer');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE document_status AS ENUM (
    'uploaded', 'queued', 'ocr_processing', 'ocr_complete',
    'validating', 'validated', 'review_needed',
    'approved', 'rejected', 'error'
  );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE document_type AS ENUM (
    'invoice', 'w9', 'bank_letter', 'contract', 'other'
  );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE review_task_status AS ENUM ('open', 'assigned', 'resolved');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE check_status AS ENUM ('processing', 'analyzed', 'error');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE verdict_type AS ENUM ('safe', 'verify', 'blocked');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE decision_type AS ENUM ('approved', 'held', 'rejected');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE signal_severity AS ENUM ('low', 'medium', 'high', 'critical');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE alert_type AS ENUM (
    'review_needed', 'pipeline_failure', 'expiry_warning', 'status_change'
  );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
  CREATE TYPE workflow_status AS ENUM ('running', 'succeeded', 'failed');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ── Helper: updated_at trigger function ──────────────────────────────────

CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ── Helper: current tenant from session variable ─────────────────────────
-- The application sets `app.tenant_id` via SET LOCAL before each transaction.

CREATE OR REPLACE FUNCTION app_tenant_id() RETURNS uuid
LANGUAGE sql STABLE
AS $$
  SELECT nullif(current_setting('app.tenant_id', true), '')::uuid
$$;

-- ═════════════════════════════════════════════════════════════════════════
-- TABLES
-- ═════════════════════════════════════════════════════════════════════════

-- ── 1. tenants ───────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS tenants (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name        TEXT NOT NULL,
  slug        TEXT NOT NULL UNIQUE,
  created_by  UUID,                                -- set after first user created
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tenants_slug ON tenants (slug);

-- ── 2. users ─────────────────────────────────────────────────────────────
-- Users exist across tenants (no tenant_id). Access is controlled via memberships.

CREATE TABLE IF NOT EXISTS users (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cognito_sub     TEXT NOT NULL UNIQUE,
  email           TEXT NOT NULL,
  display_name    TEXT NOT NULL DEFAULT '',
  email_verified  BOOLEAN NOT NULL DEFAULT false,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_users_cognito_sub ON users (cognito_sub);
CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);

-- ── 3. memberships ───────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS memberships (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role        user_role NOT NULL DEFAULT 'viewer',
  joined_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_memberships_user_id ON memberships (user_id);
CREATE INDEX IF NOT EXISTS idx_memberships_tenant_id ON memberships (tenant_id);

-- ── 4. vendors ───────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS vendors (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id     UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  name          TEXT NOT NULL,
  contact_email TEXT,
  contact_phone TEXT,
  metadata      JSONB DEFAULT '{}',
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_vendors_tenant_id ON vendors (tenant_id);
CREATE INDEX IF NOT EXISTS idx_vendors_tenant_name ON vendors (tenant_id, name);

-- ── 5. documents ─────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS documents (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id          UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  vendor_id          UUID NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
  document_type      document_type DEFAULT 'other',
  title              TEXT,
  status             document_status NOT NULL DEFAULT 'uploaded',
  current_version_no INTEGER NOT NULL DEFAULT 1 CHECK (current_version_no >= 1),
  created_by         UUID NOT NULL REFERENCES users(id),
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_documents_tenant_id ON documents (tenant_id);
CREATE INDEX IF NOT EXISTS idx_documents_vendor_id ON documents (vendor_id);
CREATE INDEX IF NOT EXISTS idx_documents_tenant_status ON documents (tenant_id, status);

-- ── 6. document_versions ─────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS document_versions (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id       UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  tenant_id         UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  version_no        INTEGER NOT NULL DEFAULT 1 CHECK (version_no >= 1),
  status            document_status NOT NULL DEFAULT 'uploaded',
  s3_bucket         TEXT,
  s3_key            TEXT,
  original_filename TEXT,
  mime_type         TEXT,
  file_size_bytes   BIGINT CHECK (file_size_bytes IS NULL OR file_size_bytes >= 0),
  sha256            TEXT,
  created_by        UUID NOT NULL REFERENCES users(id),
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (document_id, version_no)
);

CREATE INDEX IF NOT EXISTS idx_doc_versions_document_id ON document_versions (document_id);
CREATE INDEX IF NOT EXISTS idx_doc_versions_tenant_id ON document_versions (tenant_id);

-- ── 7. document_artifacts ────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS document_artifacts (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_version_id UUID NOT NULL REFERENCES document_versions(id) ON DELETE CASCADE,
  tenant_id           UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  artifact_type       TEXT NOT NULL,     -- 'ocr_text', 'ocr_json', 'extracted_text'
  s3_bucket           TEXT,
  s3_key              TEXT,
  content_text        TEXT,              -- inline for small artifacts
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_doc_artifacts_version ON document_artifacts (document_version_id);

-- ── 8. extracted_fields ──────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS extracted_fields (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_version_id UUID NOT NULL REFERENCES document_versions(id) ON DELETE CASCADE,
  tenant_id           UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  field_name          TEXT NOT NULL,
  field_value         TEXT,
  field_value_hash    TEXT,              -- SHA-256 for sensitive fields (bank numbers)
  field_value_masked  TEXT,              -- masked display value
  confidence          REAL CHECK (confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)),
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_extracted_fields_version ON extracted_fields (document_version_id);

-- ── 9. validation_results ────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS validation_results (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_version_id UUID NOT NULL REFERENCES document_versions(id) ON DELETE CASCADE,
  tenant_id           UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  validator_type      TEXT NOT NULL,     -- 'llm', 'rule_engine', 'stub'
  verdict             verdict_type,
  risk_score          INTEGER CHECK (risk_score IS NULL OR (risk_score >= 0 AND risk_score <= 100)),
  confidence          REAL CHECK (confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)),
  explanation         TEXT,
  recommended_action  TEXT,
  raw_response        JSONB,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_validation_results_version ON validation_results (document_version_id);

-- ── 10. risk_signals ─────────────────────────────────────────────────────
-- Shared across document validation and check_requests.

CREATE TABLE IF NOT EXISTS risk_signals (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id           UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  document_version_id UUID REFERENCES document_versions(id) ON DELETE CASCADE,
  check_request_id    UUID,              -- FK added after check_requests table
  signal_type         TEXT NOT NULL,
  severity            signal_severity NOT NULL,
  title               TEXT NOT NULL,
  description         TEXT NOT NULL,
  metadata            JSONB,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_risk_signals_doc_version ON risk_signals (document_version_id);
CREATE INDEX IF NOT EXISTS idx_risk_signals_tenant ON risk_signals (tenant_id);

-- ── 11. review_tasks ─────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS review_tasks (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id           UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  document_id         UUID REFERENCES documents(id) ON DELETE CASCADE,
  document_version_id UUID REFERENCES document_versions(id) ON DELETE CASCADE,
  check_request_id    UUID,              -- FK added after check_requests table
  status              review_task_status NOT NULL DEFAULT 'open',
  assigned_to         UUID REFERENCES users(id),
  priority            INTEGER DEFAULT 0,
  resolution          TEXT,
  resolved_by         UUID REFERENCES users(id),
  resolved_at         TIMESTAMPTZ,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_review_tasks_tenant ON review_tasks (tenant_id);
CREATE INDEX IF NOT EXISTS idx_review_tasks_tenant_status ON review_tasks (tenant_id, status);

-- ── 12. check_requests ───────────────────────────────────────────────────
-- The "paste text → analyze → decide" flow, now multi-tenant.

CREATE TABLE IF NOT EXISTS check_requests (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  submitted_by          UUID NOT NULL REFERENCES users(id),
  vendor_id             UUID REFERENCES vendors(id),
  input_type            TEXT NOT NULL,    -- 'paste_text', 'pdf'
  raw_input_text        TEXT,
  vendor_name           TEXT,
  vendor_contact_email  TEXT,
  vendor_contact_phone  TEXT,
  bank_name             TEXT,
  bank_account_hash     TEXT,
  bank_routing_hash     TEXT,
  bank_account_masked   TEXT,
  bank_routing_masked   TEXT,
  status                check_status NOT NULL DEFAULT 'processing',
  verdict               verdict_type,
  verdict_explanation   TEXT,
  recommended_action    TEXT,
  risk_score            INTEGER CHECK (risk_score IS NULL OR (risk_score >= 0 AND risk_score <= 100)),
  prior_check_id        UUID REFERENCES check_requests(id),
  bank_details_changed  BOOLEAN,
  analysis_error        TEXT,
  decision              decision_type,
  decided_by            UUID REFERENCES users(id),
  decided_at            TIMESTAMPTZ,
  decision_note         TEXT,
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_check_requests_tenant ON check_requests (tenant_id);
CREATE INDEX IF NOT EXISTS idx_check_requests_tenant_created ON check_requests (tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_check_requests_tenant_vendor ON check_requests (tenant_id, vendor_name);
CREATE INDEX IF NOT EXISTS idx_check_requests_tenant_status ON check_requests (tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_check_requests_tenant_verdict ON check_requests (tenant_id, verdict);

-- Deferred FK from risk_signals → check_requests
ALTER TABLE risk_signals
  DROP CONSTRAINT IF EXISTS fk_risk_signals_check_request;
ALTER TABLE risk_signals
  ADD CONSTRAINT fk_risk_signals_check_request
  FOREIGN KEY (check_request_id) REFERENCES check_requests(id) ON DELETE CASCADE;

-- Deferred FK from review_tasks → check_requests
ALTER TABLE review_tasks
  DROP CONSTRAINT IF EXISTS fk_review_tasks_check_request;
ALTER TABLE review_tasks
  ADD CONSTRAINT fk_review_tasks_check_request
  FOREIGN KEY (check_request_id) REFERENCES check_requests(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_risk_signals_check_request ON risk_signals (check_request_id);
CREATE INDEX IF NOT EXISTS idx_review_tasks_check_request ON review_tasks (check_request_id);

-- ── 13. alerts ───────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS alerts (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id      UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  alert_type     alert_type NOT NULL,
  document_id    UUID REFERENCES documents(id) ON DELETE SET NULL,
  review_task_id UUID REFERENCES review_tasks(id) ON DELETE SET NULL,
  message        TEXT NOT NULL,
  is_read        BOOLEAN NOT NULL DEFAULT false,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_alerts_tenant ON alerts (tenant_id);
CREATE INDEX IF NOT EXISTS idx_alerts_tenant_unread ON alerts (tenant_id) WHERE NOT is_read;

-- ── 14. workflow_runs ────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS workflow_runs (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id           UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  document_version_id UUID NOT NULL REFERENCES document_versions(id) ON DELETE CASCADE,
  sfn_execution_arn   TEXT,
  status              workflow_status NOT NULL DEFAULT 'running',
  started_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at        TIMESTAMPTZ,
  error_message       TEXT,
  correlation_id      UUID
);

CREATE INDEX IF NOT EXISTS idx_workflow_runs_tenant ON workflow_runs (tenant_id);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_doc_version ON workflow_runs (document_version_id);

-- ── 15. audit_logs ───────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS audit_logs (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  user_id     UUID REFERENCES users(id),
  action      TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id   UUID,
  details     JSONB,
  ip_address  INET,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_tenant ON audit_logs (tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_tenant_created ON audit_logs (tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs (entity_type, entity_id);

-- ── 16. metric_events ────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS metric_events (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  event_type  TEXT NOT NULL,
  entity_type TEXT,
  entity_id   UUID,
  value       REAL,
  metadata    JSONB,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_metric_events_tenant ON metric_events (tenant_id);
CREATE INDEX IF NOT EXISTS idx_metric_events_tenant_type ON metric_events (tenant_id, event_type);

-- ═════════════════════════════════════════════════════════════════════════
-- TRIGGERS (updated_at auto-set)
-- ═════════════════════════════════════════════════════════════════════════

DROP TRIGGER IF EXISTS set_updated_at ON tenants;
CREATE TRIGGER set_updated_at BEFORE UPDATE ON tenants
  FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

DROP TRIGGER IF EXISTS set_updated_at ON users;
CREATE TRIGGER set_updated_at BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

DROP TRIGGER IF EXISTS set_updated_at ON vendors;
CREATE TRIGGER set_updated_at BEFORE UPDATE ON vendors
  FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

DROP TRIGGER IF EXISTS set_updated_at ON documents;
CREATE TRIGGER set_updated_at BEFORE UPDATE ON documents
  FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

DROP TRIGGER IF EXISTS set_updated_at ON document_versions;
CREATE TRIGGER set_updated_at BEFORE UPDATE ON document_versions
  FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

DROP TRIGGER IF EXISTS set_updated_at ON review_tasks;
CREATE TRIGGER set_updated_at BEFORE UPDATE ON review_tasks
  FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

DROP TRIGGER IF EXISTS set_updated_at ON check_requests;
CREATE TRIGGER set_updated_at BEFORE UPDATE ON check_requests
  FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- ═════════════════════════════════════════════════════════════════════════
-- ROW LEVEL SECURITY
-- ═════════════════════════════════════════════════════════════════════════
-- Every tenant-owned table gets a policy restricting rows to app_tenant_id().
-- The `users` table is intentionally excluded — user lookup must work
-- cross-tenant for the auth/login flow. Access is app-controlled via
-- the memberships table.

ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE vendors ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_artifacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE extracted_fields ENABLE ROW LEVEL SECURITY;
ALTER TABLE validation_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE risk_signals ENABLE ROW LEVEL SECURITY;
ALTER TABLE review_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE check_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE metric_events ENABLE ROW LEVEL SECURITY;

-- Tenant isolation policies (CREATE OR REPLACE not available for policies,
-- so drop-if-exists + create).

DO $$ BEGIN
  DROP POLICY IF EXISTS tenant_isolation_tenants ON tenants;
  CREATE POLICY tenant_isolation_tenants ON tenants
    USING (id = app_tenant_id())
    WITH CHECK (id = app_tenant_id());

  DROP POLICY IF EXISTS tenant_isolation_memberships ON memberships;
  CREATE POLICY tenant_isolation_memberships ON memberships
    USING (tenant_id = app_tenant_id())
    WITH CHECK (tenant_id = app_tenant_id());

  DROP POLICY IF EXISTS tenant_isolation_vendors ON vendors;
  CREATE POLICY tenant_isolation_vendors ON vendors
    USING (tenant_id = app_tenant_id())
    WITH CHECK (tenant_id = app_tenant_id());

  DROP POLICY IF EXISTS tenant_isolation_documents ON documents;
  CREATE POLICY tenant_isolation_documents ON documents
    USING (tenant_id = app_tenant_id())
    WITH CHECK (tenant_id = app_tenant_id());

  DROP POLICY IF EXISTS tenant_isolation_document_versions ON document_versions;
  CREATE POLICY tenant_isolation_document_versions ON document_versions
    USING (tenant_id = app_tenant_id())
    WITH CHECK (tenant_id = app_tenant_id());

  DROP POLICY IF EXISTS tenant_isolation_document_artifacts ON document_artifacts;
  CREATE POLICY tenant_isolation_document_artifacts ON document_artifacts
    USING (tenant_id = app_tenant_id())
    WITH CHECK (tenant_id = app_tenant_id());

  DROP POLICY IF EXISTS tenant_isolation_extracted_fields ON extracted_fields;
  CREATE POLICY tenant_isolation_extracted_fields ON extracted_fields
    USING (tenant_id = app_tenant_id())
    WITH CHECK (tenant_id = app_tenant_id());

  DROP POLICY IF EXISTS tenant_isolation_validation_results ON validation_results;
  CREATE POLICY tenant_isolation_validation_results ON validation_results
    USING (tenant_id = app_tenant_id())
    WITH CHECK (tenant_id = app_tenant_id());

  DROP POLICY IF EXISTS tenant_isolation_risk_signals ON risk_signals;
  CREATE POLICY tenant_isolation_risk_signals ON risk_signals
    USING (tenant_id = app_tenant_id())
    WITH CHECK (tenant_id = app_tenant_id());

  DROP POLICY IF EXISTS tenant_isolation_review_tasks ON review_tasks;
  CREATE POLICY tenant_isolation_review_tasks ON review_tasks
    USING (tenant_id = app_tenant_id())
    WITH CHECK (tenant_id = app_tenant_id());

  DROP POLICY IF EXISTS tenant_isolation_check_requests ON check_requests;
  CREATE POLICY tenant_isolation_check_requests ON check_requests
    USING (tenant_id = app_tenant_id())
    WITH CHECK (tenant_id = app_tenant_id());

  DROP POLICY IF EXISTS tenant_isolation_alerts ON alerts;
  CREATE POLICY tenant_isolation_alerts ON alerts
    USING (tenant_id = app_tenant_id())
    WITH CHECK (tenant_id = app_tenant_id());

  DROP POLICY IF EXISTS tenant_isolation_workflow_runs ON workflow_runs;
  CREATE POLICY tenant_isolation_workflow_runs ON workflow_runs
    USING (tenant_id = app_tenant_id())
    WITH CHECK (tenant_id = app_tenant_id());

  DROP POLICY IF EXISTS tenant_isolation_audit_logs ON audit_logs;
  CREATE POLICY tenant_isolation_audit_logs ON audit_logs
    USING (tenant_id = app_tenant_id())
    WITH CHECK (tenant_id = app_tenant_id());

  DROP POLICY IF EXISTS tenant_isolation_metric_events ON metric_events;
  CREATE POLICY tenant_isolation_metric_events ON metric_events
    USING (tenant_id = app_tenant_id())
    WITH CHECK (tenant_id = app_tenant_id());
END $$;

COMMIT;
