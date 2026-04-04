-- VendorCheck: Row Level Security policies for multi-tenant isolation
-- Migration: 002_rls.sql
-- Prerequisite: 001_init.sql

-- ── Tenant resolution function ───────────────────────────
-- The application sets `app.tenant_id` via SET LOCAL before each transaction.

CREATE OR REPLACE FUNCTION app_tenant_id() RETURNS uuid
LANGUAGE sql STABLE
AS $$
  SELECT nullif(current_setting('app.tenant_id', true), '')::uuid
$$;

-- ── Enable RLS on all tenant-owned tables ────────────────

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

-- ── Tenant isolation policies ────────────────────────────
-- Each policy restricts SELECT/INSERT/UPDATE/DELETE to rows matching app_tenant_id().

-- tenants: can only see own tenant
CREATE POLICY tenant_isolation_tenants ON tenants
  USING (id = app_tenant_id())
  WITH CHECK (id = app_tenant_id());

-- memberships
CREATE POLICY tenant_isolation_memberships ON memberships
  USING (tenant_id = app_tenant_id())
  WITH CHECK (tenant_id = app_tenant_id());

-- vendors
CREATE POLICY tenant_isolation_vendors ON vendors
  USING (tenant_id = app_tenant_id())
  WITH CHECK (tenant_id = app_tenant_id());

-- documents
CREATE POLICY tenant_isolation_documents ON documents
  USING (tenant_id = app_tenant_id())
  WITH CHECK (tenant_id = app_tenant_id());

-- document_versions
CREATE POLICY tenant_isolation_document_versions ON document_versions
  USING (tenant_id = app_tenant_id())
  WITH CHECK (tenant_id = app_tenant_id());

-- document_artifacts
CREATE POLICY tenant_isolation_document_artifacts ON document_artifacts
  USING (tenant_id = app_tenant_id())
  WITH CHECK (tenant_id = app_tenant_id());

-- extracted_fields
CREATE POLICY tenant_isolation_extracted_fields ON extracted_fields
  USING (tenant_id = app_tenant_id())
  WITH CHECK (tenant_id = app_tenant_id());

-- validation_results
CREATE POLICY tenant_isolation_validation_results ON validation_results
  USING (tenant_id = app_tenant_id())
  WITH CHECK (tenant_id = app_tenant_id());

-- risk_signals
CREATE POLICY tenant_isolation_risk_signals ON risk_signals
  USING (tenant_id = app_tenant_id())
  WITH CHECK (tenant_id = app_tenant_id());

-- review_tasks
CREATE POLICY tenant_isolation_review_tasks ON review_tasks
  USING (tenant_id = app_tenant_id())
  WITH CHECK (tenant_id = app_tenant_id());

-- check_requests
CREATE POLICY tenant_isolation_check_requests ON check_requests
  USING (tenant_id = app_tenant_id())
  WITH CHECK (tenant_id = app_tenant_id());

-- alerts
CREATE POLICY tenant_isolation_alerts ON alerts
  USING (tenant_id = app_tenant_id())
  WITH CHECK (tenant_id = app_tenant_id());

-- workflow_runs
CREATE POLICY tenant_isolation_workflow_runs ON workflow_runs
  USING (tenant_id = app_tenant_id())
  WITH CHECK (tenant_id = app_tenant_id());

-- audit_logs
CREATE POLICY tenant_isolation_audit_logs ON audit_logs
  USING (tenant_id = app_tenant_id())
  WITH CHECK (tenant_id = app_tenant_id());

-- metric_events
CREATE POLICY tenant_isolation_metric_events ON metric_events
  USING (tenant_id = app_tenant_id())
  WITH CHECK (tenant_id = app_tenant_id());

-- ── Note on users table ──────────────────────────────────
-- The `users` table does NOT have tenant_id (users exist across tenants).
-- Access to user rows is controlled at the application level via memberships.
-- RLS is NOT enabled on users — the app backend uses a service role that
-- needs cross-tenant user lookup for auth.
