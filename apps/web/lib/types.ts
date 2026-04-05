// API response types — mirrors FastAPI Pydantic schemas

// ---- Auth / Me ----
export interface Workspace {
  id: string;
  name: string;
  slug: string;
  role: string;
}

export interface MeResponse {
  user_id: string;
  email: string;
  display_name: string;
  workspace: Workspace;
}

// ---- Checks ----
export interface Signal {
  id: string;
  signal_type: string;
  severity: "low" | "medium" | "high" | "critical";
  title: string;
  description: string;
}

export interface SubmittedBy {
  id: string;
  display_name: string;
}

export interface CheckListItem {
  id: string;
  status: string;
  input_type: string;
  vendor_name: string | null;
  verdict: string | null;
  risk_score: number | null;
  decision: string | null;
  created_at: string;
}

export interface CheckListResponse {
  items: CheckListItem[];
}

export interface CheckDetail {
  id: string;
  status: string;
  input_type: string;
  vendor_name: string | null;
  vendor_contact_email: string | null;
  vendor_contact_phone: string | null;
  bank_name: string | null;
  bank_account_masked: string | null;
  bank_routing_masked: string | null;
  bank_details_changed: boolean | null;
  verdict: string | null;
  verdict_explanation: string | null;
  recommended_action: string | null;
  risk_score: number | null;
  signals: Signal[];
  prior_check_id: string | null;
  decision: string | null;
  decision_note: string | null;
  decided_at: string | null;
  analysis_error: string | null;
  submitted_by: SubmittedBy;
  created_at: string;
  raw_input_text: string | null;
}

export interface CreateCheckResponse extends CheckDetail {}

export interface CheckDecisionResponse {
  check_id: string;
  decision: string;
  decided_by: string;
  decided_at: string;
}

// ---- Vendors ----
export interface Vendor {
  id: string;
  name: string;
  contact_email: string | null;
  contact_phone: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

export interface VendorListResponse {
  items: Vendor[];
}

// ---- Documents ----
export interface DocumentItem {
  id: string;
  vendor_id: string;
  document_type: string | null;
  title: string | null;
  status: string;
  current_version_no: number;
  created_at: string;
}

export interface DocumentListResponse {
  items: DocumentItem[];
}

export interface InitiateUploadResponse {
  document_id: string;
  document_version_id: string;
  upload_url: string;
  s3_key: string;
}

// ---- Reviews ----
export interface ReviewTask {
  id: string;
  document_id: string | null;
  check_request_id: string | null;
  status: string;
  assigned_to: string | null;
  priority: number;
  resolution: string | null;
  resolved_by: string | null;
  resolved_at: string | null;
  created_at: string;
}

export interface ReviewTaskListResponse {
  items: ReviewTask[];
}

// ---- Metrics ----
export interface MetricsSummary {
  total_vendors: number;
  total_documents: number;
  total_checks: number;
  open_review_tasks: number;
  decisions_approved: number;
  decisions_held: number;
  decisions_rejected: number;
}
