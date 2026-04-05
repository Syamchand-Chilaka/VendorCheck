import { getIdToken } from "./auth";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

class ApiError extends Error {
  constructor(
    public status: number,
    public body: unknown,
  ) {
    super(`API ${status}`);
    this.name = "ApiError";
  }
}

async function headers(tenantId?: string): Promise<Record<string, string>> {
  const h: Record<string, string> = { "Content-Type": "application/json" };
  const token = await getIdToken();
  if (token) h["Authorization"] = `Bearer ${token}`;
  if (tenantId) h["X-Tenant-Id"] = tenantId;
  return h;
}

async function request<T>(
  method: string,
  path: string,
  opts?: { body?: unknown; tenantId?: string; formData?: FormData },
): Promise<T> {
  const h = await headers(opts?.tenantId);
  if (opts?.formData) delete h["Content-Type"]; // browser sets multipart boundary

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: h,
    body: opts?.formData ?? (opts?.body ? JSON.stringify(opts.body) : undefined),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(res.status, body);
  }

  return res.json() as Promise<T>;
}

// ---- typed wrappers ----
import type {
  MeResponse,
  CheckListResponse,
  CheckDetail,
  CheckDecisionResponse,
  Vendor,
  VendorListResponse,
  DocumentListResponse,
  InitiateUploadResponse,
  ReviewTaskListResponse,
  MetricsSummary,
} from "./types";

export { ApiError };

// Me
export const getMe = (tid: string) =>
  request<MeResponse>("GET", "/api/v1/me", { tenantId: tid });

// Checks
export const listChecks = (tid: string) =>
  request<CheckListResponse>("GET", "/api/v1/checks", { tenantId: tid });

export const getCheck = (tid: string, id: string) =>
  request<CheckDetail>("GET", `/api/v1/checks/${encodeURIComponent(id)}`, {
    tenantId: tid,
  });

export const createCheck = (tid: string, formData: FormData) =>
  request<CheckDetail>("POST", "/api/v1/checks", {
    tenantId: tid,
    formData,
  });

export const decideCheck = (
  tid: string,
  id: string,
  decision: string,
  note?: string,
) =>
  request<CheckDecisionResponse>(
    "POST",
    `/api/v1/checks/${encodeURIComponent(id)}/decision`,
    { tenantId: tid, body: { decision, note } },
  );

// Vendors
export const listVendors = (tid: string) =>
  request<VendorListResponse>("GET", "/api/v1/vendors", { tenantId: tid });

export const createVendor = (
  tid: string,
  data: { name: string; contact_email?: string; contact_phone?: string },
) =>
  request<Vendor>("POST", "/api/v1/vendors", { tenantId: tid, body: data });

// Documents
export const listDocuments = (tid: string) =>
  request<DocumentListResponse>("GET", "/api/v1/documents", { tenantId: tid });

export const initiateUpload = (
  tid: string,
  data: {
    vendor_id: string;
    document_type: string;
    title: string;
    original_filename: string;
    mime_type: string;
    file_size_bytes: number;
  },
) =>
  request<InitiateUploadResponse>("POST", "/api/v1/documents/upload-initiate", {
    tenantId: tid,
    body: data,
  });

// Reviews
export const listReviewTasks = (tid: string) =>
  request<ReviewTaskListResponse>("GET", "/api/v1/review-tasks", {
    tenantId: tid,
  });

export const resolveReviewTask = (
  tid: string,
  id: string,
  resolution: string,
) =>
  request<unknown>(
    "POST",
    `/api/v1/review-tasks/${encodeURIComponent(id)}/resolve`,
    { tenantId: tid, body: { resolution } },
  );

// Metrics
export const getMetrics = (tid: string) =>
  request<MetricsSummary>("GET", "/api/v1/metrics/summary", { tenantId: tid });
