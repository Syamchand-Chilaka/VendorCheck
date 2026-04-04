-- VendorCheck: Initial multi-tenant schema
-- Migration: 001_init.sql
-- Targets: Amazon RDS PostgreSQL 16

-- ── Extensions ───────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── Enums ────────────────────────────────────────────────

CREATE TYPE user_role AS ENUM ('owner', 'admin', 'reviewer', 'member');
CREATE TYPE document_status AS ENUM (
  'uploaded', 'queued', 'ocr_processing', 'ocr_complete',
  'validating', 'validated', 'review_needed',
  'approved', 'rejected', 'error'
);
CREATE TYPE document_type AS ENUM ('invoice', 'w9', 'bank_letter', 'contract', 'other');
CREATE TYPE review_task_status AS ENUM ('open', 'assigned', 'resolved');
CREATE TYPE check_status AS ENUM ('processing', 'analyzed', 'error');
CREATE TYPE verdict_type AS ENUM ('safe', 'verify', 'blocked');
CREATE TYPE decision_type AS ENUM ('approved', 'held', 'rejected');
CREATE TYPE signal_severity AS ENUM ('low', 'medium', 'high', 'critical');
CREATE TYPE alert_type AS ENUM ('review_needed', 'pipeline_failure', 'expiry_warning', 'status_change');

-- ── 1. tenants ───────────────────────────────────────────

CREATE TABLE tenants (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name        TEXT NOT NULL,
  slug        TEXT NOT NULL UNIQUE,
  created_by  UUID,  -- references users.id, set after first user created
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_tenants_slug ON tenants (slug);

-- ── 2. users ─────────────────────────────────────────────

CREATE TABLE users (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cognito_sub   TEXT NOT NULL UNIQUE,
  email         TEXT NOT NULL,
  display_name  TEXT NOT NULL DEFAULT '',
  email_verified BOOLEAN NOT NULL DEFAULT false,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_users_cognito_sub ON users (cognito_sub);
CREATE INDEX idx_users_email ON users (email);

-- ── 3. memberships ───────────────────────────────────────

CREATE TABLE memberships (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role        user_role NOT NULL DEFAULT 'member',
  joined_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, user_id)
);

CREATE INDEX idx_memberships_user_id ON memberships (user_id);
CREATE INDEX idx_memberships_tenant_id ON memberships (tenant_id);

-- ── 4. vendors ───────────────────────────────────────────

CREATE TABLE vendors (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id    UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  name         TEXT NOT NULL,
  contact_email TEXT,
  contact_phone TEXT,
  metadata     JSONB DEFAULT '{}',
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_vendors_tenant_id ON vendors (tenant_id);
CREATE INDEX idx_vendors_tenant_name ON vendors (tenant_id, name);

-- ── 5. documents ─────────────────────────────────────────

CREATE TABLE documents (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id      UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  vendor_id      UUID NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
  document_type  document_type DEFAULT 'other',
  title          TEXT,
  status         document_status NOT NULL DEFAULT 'uploaded',
  current_version_no INTEGER NOT NULL DEFAULT 1,
  created_by     UUID NOT NULL REFERENCES users(id),
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_documents_tenant_id ON documents (tenant_id);
CREATE INDEX idx_documents_vendor_id ON documents (vendor_id);
CREATE INDEX idx_documents_tenant_status ON documents (tenant_id, status);

-- ── 6. document_versions ─────────────────────────────────

CREATE TABLE document_versions (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id     UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  version_no      INTEGER NOT NULL DEFAULT 1,
  status          document_status NOT NULL DEFAULT 'uploaded',
  s3_bucket       TEXT,
  s3_key          TEXT,
  original_filename TEXT,
  mime_type       TEXT,
  file_size_bytes BIGINT,
  sha256          TEXT,
  created_by      UUID NOT NULL REFERENCES users(id),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (document_id, version_no)
);

CREATE INDEX idx_doc_versions_document_id ON document_versions (document_id);
CREATE INDEX idx_doc_versions_tenant_id ON document_versions (tenant_id);

-- ── 7. document_artifacts ────────────────────────────────

CREATE TABLE document_artifacts (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_version_id UUID NOT NULL REFERENCES document_versions(id) ON DELETE CASCADE,
  tenant_id           UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  artifact_type       TEXT NOT NULL,  -- 'ocr_text', 'ocr_json', 'extracted_text'
  s3_bucket           TEXT,
  s3_key              TEXT,
  content_text        TEXT,           -- inline for small artifacts
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_doc_artifacts_version ON document_artifacts (document_version_id);

-- ── 8. extracted_fields ──────────────────────────────────

CREATE TABLE extracted_fields (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_version_id UUID NOT NULL REFERENCES document_versions(id) ON DELETE CASCADE,
  tenant_id           UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  field_name          TEXT NOT NULL,
  field_value         TEXT,
  field_value_hash    TEXT,       -- SHA-256 for sensitive fields (bank numbers)
  field_value_masked  TEXT,       -- masked display value
  confidence          REAL,      -- 0.0 to 1.0
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_extracted_fields_version ON extracted_fields (document_version_id);

-- ── 9. validation_results ────────────────────────────────

CREATE TABLE validation_results (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_version_id UUID NOT NULL REFERENCES document_versions(id) ON DELETE CASCADE,
  tenant_id           UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  validator_type      TEXT NOT NULL,  -- 'llm', 'rule_engine', 'stub'
  verdict             verdict_type,
  risk_score          INTEGER,       -- 0-100
  confidence          REAL,          -- 0.0-1.0
  explanation         TEXT,
  recommended_action  TEXT,
  raw_response        JSONB,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_validation_results_version ON validation_results (document_version_id);

-- ── 10. risk_signals ─────────────────────────────────────
-- Used by both document validation and legacy check_requests

CREATE TABLE risk_signals (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id           UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  document_version_id UUID REFERENCES document_versions(id) ON DELETE CASCADE,
  check_request_id    UUID,  -- FK added after check_requests table created
  signal_type         TEXT NOT NULL,
  severity            signal_severity NOT NULL,
  title               TEXT NOT NULL,
  description         TEXT NOT NULL,
  metadata            JSONB,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_risk_signals_doc_version ON risk_signals (document_version_id);
CREATE INDEX idx_risk_signals_tenant ON risk_signals (tenant_id);

-- ── 11. review_tasks ─────────────────────────────────────

CREATE TABLE review_tasks (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id           UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  document_id         UUID REFERENCES documents(id) ON DELETE CASCADE,
  document_version_id UUID REFERENCES document_versions(id) ON DELETE CASCADE,
  check_request_id    UUID,  -- FK added after check_requests table created
  status              review_task_status NOT NULL DEFAULT 'open',
  assigned_to         UUID REFERENCES users(id),
  priority            INTEGER DEFAULT 0,
  resolution          TEXT,
  resolved_by         UUID REFERENCES users(id),
  resolved_at         TIMESTAMPTZ,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_review_tasks_tenant ON review_tasks (tenant_id);
CREATE INDEX idx_review_tasks_tenant_status ON review_tasks (tenant_id, status);

-- ── 12. check_requests (legacy checks, now tenant-scoped) ──

CREATE TABLE check_requests (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id             UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  submitted_by          UUID NOT NULL REFERENCES users(id),
  vendor_id             UUID REFERENCES vendors(id),
  input_type            TEXT NOT NULL,  -- 'paste_text', 'pdf'
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
  risk_score            INTEGER,
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

CREATE INDEX idx_check_requests_tenant ON check_requests (tenant_id);
CREATE INDEX idx_check_requests_tenant_created ON check_requests (tenant_id, created_at DESC);
CREATE INDEX idx_check_requests_tenant_vendor ON check_requests (tenant_id, vendor_name);
CREATE INDEX idx_check_requests_tenant_status ON check_requests (tenant_id, status);
CREATE INDEX idx_check_requests_tenant_verdict ON check_requests (tenant_id, verdict);

-- Add FK from risk_signals and review_tasks to check_requests
ALTER TABLE risk_signals
  ADD CONSTRAINT fk_risk_signals_check_request
  FOREIGN KEY (check_request_id) REFERENCES check_requests(id) ON DELETE CASCADE;

ALTER TABLE review_tasks
  ADD CONSTRAINT fk_review_tasks_check_request
  FOREIGN KEY (check_request_id) REFERENCES check_requests(id) ON DELETE CASCADE;

CREATE INDEX idx_risk_signals_check_request ON risk_signals (check_request_id);

-- ── 13. alerts ───────────────────────────────────────────

CREATE TABLE alerts (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id      UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  alert_type     alert_type NOT NULL,
  document_id    UUID REFERENCES documents(id) ON DELETE SET NULL,
  review_task_id UUID REFERENCES review_tasks(id) ON DELETE SET NULL,
  message        TEXT NOT NULL,
  is_read        BOOLEAN NOT NULL DEFAULT false,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_alerts_tenant ON alerts (tenant_id);
CREATE INDEX idx_alerts_tenant_unread ON alerts (tenant_id) WHERE NOT is_read;

-- ── 14. workflow_runs ────────────────────────────────────

CREATE TABLE workflow_runs (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id           UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  document_version_id UUID NOT NULL REFERENCES document_versions(id) ON DELETE CASCADE,
  sfn_execution_arn   TEXT,
  status              TEXT NOT NULL DEFAULT 'running',  -- running, succeeded, failed
  started_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at        TIMESTAMPTZ,
  error_message       TEXT,
  correlation_id      UUID
);

CREATE INDEX idx_workflow_runs_tenant ON workflow_runs (tenant_id);
CREATE INDEX idx_workflow_runs_doc_version ON workflow_runs (document_version_id);

-- ── 15. audit_logs ───────────────────────────────────────

CREATE TABLE audit_logs (
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

CREATE INDEX idx_audit_logs_tenant ON audit_logs (tenant_id);
CREATE INDEX idx_audit_logs_tenant_created ON audit_logs (tenant_id, created_at DESC);
CREATE INDEX idx_audit_logs_entity ON audit_logs (entity_type, entity_id);

-- ── 16. metric_events ────────────────────────────────────

CREATE TABLE metric_events (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  event_type  TEXT NOT NULL,
  entity_type TEXT,
  entity_id   UUID,
  value       REAL,
  metadata    JSONB,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_metric_events_tenant ON metric_events (tenant_id);
CREATE INDEX idx_metric_events_tenant_type ON metric_events (tenant_id, event_type);

-- ── Updated-at triggers ──────────────────────────────────

CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_updated_at BEFORE UPDATE ON tenants
  FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER set_updated_at BEFORE UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER set_updated_at BEFORE UPDATE ON vendors
  FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER set_updated_at BEFORE UPDATE ON documents
  FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER set_updated_at BEFORE UPDATE ON document_versions
  FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER set_updated_at BEFORE UPDATE ON review_tasks
  FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

CREATE TRIGGER set_updated_at BEFORE UPDATE ON check_requests
  FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
