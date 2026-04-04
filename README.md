# VendorCheck

Multi-tenant B2B SaaS for vendor compliance and document management. AI-assisted risk analysis with human-in-the-loop review for vendor payment verification.

## Architecture

AWS-first, multi-tenant (pooled RDS with RLS). See [docs/architecture/overview.md](docs/architecture/overview.md) for full details.

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, React 19, Tailwind v4 |
| Backend API | FastAPI (Python 3.11+) |
| Workers | AWS Lambda |
| Pipeline | AWS Step Functions |
| Auth | Amazon Cognito |
| Database | Amazon RDS PostgreSQL |
| Storage | Amazon S3 |
| Alerts | Amazon SNS |
| OCR | PaddleOCR |
| LLM | Ollama (dev) / vLLM (prod) |

## Repository Structure

```
VendorCheck/
├── apps/
│   ├── api/              # FastAPI backend
│   │   ├── app/          #   Application code
│   │   │   ├── models/   #     Domain enums and types
│   │   │   ├── routes/   #     API route handlers
│   │   │   ├── schemas/  #     Pydantic request/response models
│   │   │   └── services/ #     Business logic layer
│   │   └── tests/        #   Backend tests
│   ├── web/              # Next.js frontend (landing page + app UI)
│   │   └── app/          #   Next.js app directory
│   └── workers/          # Lambda handlers for event-driven processing
├── db/
│   ├── migrations/       # PostgreSQL schema migrations
│   └── seeds/            # Dev seed data
├── infra/
│   └── terraform/        # Infrastructure as code
│       ├── modules/      #   Reusable Terraform modules
│       └── envs/dev/     #   Dev environment configuration
├── docs/
│   ├── architecture/     # Architecture documentation
│   ├── api/              # API documentation
│   ├── v1-schema-and-api-contract.md
│   └── v1-implementation-plan.md
└── scripts/              # Dev and ops scripts
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- Terraform 1.5+
- AWS CLI configured
- Docker (for local Ollama)

### Backend Dev Server

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # Then fill in credentials
uvicorn app.main:app --reload --port 8000
```

### Frontend Dev Server

```bash
cd apps/web
npm install
npm run dev
```

### Run Backend Tests

```bash
cd apps/api
source .venv/bin/activate
pytest -v
```

### Infrastructure (Terraform)

```bash
cd infra/terraform/envs/dev
terraform init
terraform plan
terraform apply
```

See [infra/terraform/README.md](infra/terraform/README.md) for details.

## Key Features

- Vendor bank-detail change detection
- Urgency language and fraud signal detection
- Risk scoring with Safe / Verify / Blocked verdicts
- Human-in-the-loop review workflow
- Multi-tenant workspace isolation
- Immutable audit trail
- Document processing pipeline (OCR + LLM validation)