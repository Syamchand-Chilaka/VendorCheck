-- VendorCheck: Dev seed data
-- Seed: 001_dev_seed.sql
-- Prerequisite: 001_init.sql, 002_rls.sql

-- Temporarily disable RLS for seeding (we're using the superuser role)
SET session_replication_role = 'replica';

-- ── Tenant ───────────────────────────────────────────────
INSERT INTO tenants (id, name, slug) VALUES
  ('a0000000-0000-0000-0000-000000000001', 'Acme Property Management', 'acme-property');

-- ── User (will be linked to Cognito sub on first login) ──
INSERT INTO users (id, cognito_sub, email, display_name, email_verified) VALUES
  ('b0000000-0000-0000-0000-000000000001', 'dev-cognito-sub-placeholder', 'admin@acme-property.example', 'Dev Admin', true);

-- Set tenant creator
UPDATE tenants SET created_by = 'b0000000-0000-0000-0000-000000000001'
  WHERE id = 'a0000000-0000-0000-0000-000000000001';

-- ── Membership (owner) ───────────────────────────────────
INSERT INTO memberships (id, tenant_id, user_id, role) VALUES
  ('c0000000-0000-0000-0000-000000000001',
   'a0000000-0000-0000-0000-000000000001',
   'b0000000-0000-0000-0000-000000000001',
   'owner');

-- ── Vendor ───────────────────────────────────────────────
INSERT INTO vendors (id, tenant_id, name, contact_email, contact_phone) VALUES
  ('d0000000-0000-0000-0000-000000000001',
   'a0000000-0000-0000-0000-000000000001',
   'Greenfield Plumbing LLC',
   'billing@greenfield-plumbing.example',
   '555-012-3456');

-- ── Document + Version ───────────────────────────────────
INSERT INTO documents (id, tenant_id, vendor_id, document_type, title, status, created_by) VALUES
  ('e0000000-0000-0000-0000-000000000001',
   'a0000000-0000-0000-0000-000000000001',
   'd0000000-0000-0000-0000-000000000001',
   'invoice',
   'January 2026 Invoice',
   'uploaded',
   'b0000000-0000-0000-0000-000000000001');

INSERT INTO document_versions (id, document_id, tenant_id, version_no, status, original_filename, mime_type, file_size_bytes, created_by) VALUES
  ('f0000000-0000-0000-0000-000000000001',
   'e0000000-0000-0000-0000-000000000001',
   'a0000000-0000-0000-0000-000000000001',
   1,
   'uploaded',
   'greenfield-jan-2026-invoice.pdf',
   'application/pdf',
   45321,
   'b0000000-0000-0000-0000-000000000001');

-- Re-enable RLS
SET session_replication_role = 'origin';
