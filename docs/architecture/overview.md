# VendorCheck — Architecture Overview

## System Model

VendorCheck is a **multi-tenant B2B SaaS** for vendor compliance, document management, and payment-risk verification.

Each customer company is a **tenant** (workspace). Users authenticate, upload vendor documents, and run compliance checks with AI-assisted risk analysis and human-in-the-loop review.

## Architecture

```
                        ┌──────────────┐
                        │   Cognito    │  Identity & Auth
                        └──────┬───────┘
                               │ JWT
          ┌────────────────────┼────────────────────┐
          │                    │                     │
    ┌─────▼─────┐       ┌─────▼─────┐         ┌────▼─────┐
    │  Next.js  │       │  FastAPI  │         │  Lambda  │
    │  Frontend │◄─────►│  Backend  │         │  Workers │
    └───────────┘ REST  └─────┬─────┘         └────┬─────┘
                              │                     │
                    ┌─────────┼─────────┐           │
                    │         │         │           │
              ┌─────▼───┐ ┌──▼──┐ ┌───▼───┐  ┌───▼──────────┐
              │   RDS   │ │ S3  │ │  SNS  │  │ Step Functions│
              │Postgres │ │Docs │ │Alerts │  │  Pipeline     │
              └─────────┘ └─────┘ └───────┘  └──────────────┘
```

## Tenancy Model

- **Pooled multi-tenancy:** Single RDS PostgreSQL instance, shared schema, `tenant_id` column on every tenant-owned table.
- **Row Level Security (RLS):** Enforced via `SET LOCAL app.tenant_id` per transaction.
- **Future option:** Bridge or silo tenancy for high-value customers.

## AWS Services

| Service | Purpose |
|---------|---------|
| **Amazon Cognito** | User Pool for authentication. Email/password. JWT tokens. |
| **Amazon RDS PostgreSQL** | System of record. All tenant data, metadata, audit logs. |
| **Amazon S3** | Document storage — raw PDFs, OCR artifacts. |
| **AWS Lambda** | Event-driven processing on S3 uploads. |
| **AWS Step Functions** | Document processing pipeline orchestration. |
| **Amazon SNS** | Alert fan-out on review tasks, failures, expiry. |

## AI Stack

| Component | Purpose |
|-----------|---------|
| **PaddleOCR** | Document text extraction (OCR) |
| **Ollama** | Local/dev LLM for validation |
| **vLLM** | Production inference for document validation |
| **Human review** | Low confidence exceptions routed to reviewers |

## Document Processing Pipeline

1. User authenticates via Cognito, selects tenant workspace.
2. User uploads a vendor document (PDF) — gets presigned S3 URL.
3. App writes initial metadata to RDS.
4. S3 `ObjectCreated` triggers Lambda.
5. Lambda starts Step Functions state machine.
6. State machine pipeline:
   - **RunOCR** — PaddleOCR text extraction.
   - **StoreOCRArtifacts** — Save text/JSON to S3 + RDS.
   - **RunValidation** — LLM validation (Ollama dev / vLLM prod).
   - **UpdateDocumentStatus** — Confidence, field extraction.
   - **RouteReviewOrApprove** — Auto-approve or create review task.
   - **PublishAlert** — SNS notification on failure/review needed.
7. Reviewers handle tasks; audit logs and metrics written.

## Key Business Concepts

- **Vendor compliance checks:** Bank change detection, risk scoring.
- **Verdicts:** Safe / Verify / Blocked.
- **Decisions:** Approve / Hold / Reject (immutable per check).
- **Risk signals:** bank_change_detected, urgency_language, domain_mismatch, missing_fields, etc.
- **Audit trail:** All decisions and status changes are logged.
