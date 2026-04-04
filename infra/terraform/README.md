# VendorCheck — Terraform Infrastructure

## Overview

Terraform modules for the VendorCheck AWS infrastructure.

## Modules

| Module | Resources |
|--------|-----------|
| `cognito` | Cognito User Pool + app client |
| `rds_postgres` | RDS PostgreSQL instance + parameter group |
| `s3_documents` | S3 bucket (private, versioned, encrypted) |
| `sns_alerts` | SNS topic for alert fan-out |
| `lambda` | Lambda function for S3 → pipeline trigger |
| `step_functions` | Step Functions state machine for doc processing |
| `iam` | IAM roles and policies for Lambda + Step Functions |

Bucket notifications are declared at the environment layer instead of inside the
S3 module to avoid a Terraform dependency cycle between the S3 and Lambda modules.

## Dev Environment Setup

### Prerequisites

- [Terraform >= 1.5](https://www.terraform.io/downloads)
- AWS CLI configured with appropriate credentials
- An AWS account with permissions to create the above resources

### Steps

```bash
cd infra/terraform/envs/dev

# Copy and edit variables
cp dev.tfvars.example dev.tfvars
# Edit dev.tfvars with your RDS password and optional alert email

# Initialize
terraform init

# Preview changes
terraform plan -var-file=dev.tfvars

# Apply
terraform apply -var-file=dev.tfvars
```

### Outputs

After apply, Terraform outputs the values needed for the backend `.env`:

| Output | Maps to .env var |
|--------|-----------------|
| `aws_region` | `AWS_REGION` |
| `cognito_user_pool_id` | `COGNITO_USER_POOL_ID` |
| `cognito_user_pool_client_id` | `COGNITO_USER_POOL_CLIENT_ID` |
| `cognito_jwks_url` | (derivable from pool ID) |
| `s3_documents_bucket` | `S3_DOCUMENTS_BUCKET` |
| `rds_host` | part of `DATABASE_URL` |
| `rds_port` | part of `DATABASE_URL` |
| `rds_db_name` | part of `DATABASE_URL` |
| `rds_database_url` | `DATABASE_URL` (sensitive) |
| `sns_alerts_topic_arn` | `SNS_ALERTS_TOPIC_ARN` |
| `step_functions_state_machine_arn` | `STEP_FUNCTIONS_STATE_MACHINE_ARN` |

To view sensitive outputs:

```bash
terraform output -raw rds_database_url
```

### Tear Down

```bash
terraform destroy -var-file=dev.tfvars
```

## Cost Notes (Dev)

- RDS `db.t3.micro` — ~$12/month (on-demand) or Free Tier eligible
- Lambda — Free Tier covers 1M requests/month
- S3 — negligible at dev scale
- Cognito — Free Tier covers 50K MAU
- Step Functions — Free Tier covers 4K transitions/month
- SNS — Free Tier covers 1M publishes/month
