terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ── Variables ─────────────────────────────────────────────

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project" {
  type    = string
  default = "vendorcheck"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "rds_password" {
  type      = string
  sensitive = true
}

variable "alert_email" {
  type    = string
  default = ""
}

# ── Modules ───────────────────────────────────────────────

module "cognito" {
  source      = "../../modules/cognito"
  project     = var.project
  environment = var.environment
}

module "rds" {
  source         = "../../modules/rds_postgres"
  project        = var.project
  environment    = var.environment
  db_password    = var.rds_password
  instance_class = "db.t3.micro"
}

module "s3" {
  source              = "../../modules/s3_documents"
  project             = var.project
  environment         = var.environment
  lambda_function_arn = module.lambda.function_arn
}

module "sns" {
  source      = "../../modules/sns_alerts"
  project     = var.project
  environment = var.environment
  alert_email = var.alert_email
}

module "iam" {
  source        = "../../modules/iam"
  project       = var.project
  environment   = var.environment
  s3_bucket_arn = module.s3.bucket_arn
  sns_topic_arn = module.sns.topic_arn
}

module "step_functions" {
  source        = "../../modules/step_functions"
  project       = var.project
  environment   = var.environment
  sfn_role_arn  = module.iam.step_functions_role_arn
  sns_topic_arn = module.sns.topic_arn
}

module "lambda" {
  source             = "../../modules/lambda"
  project            = var.project
  environment        = var.environment
  s3_bucket_arn      = module.s3.bucket_arn
  s3_bucket_name     = module.s3.bucket_name
  rds_database_url   = module.rds.database_url
  step_functions_arn = module.step_functions.state_machine_arn
  lambda_role_arn    = module.iam.lambda_role_arn
}

# ── Outputs ───────────────────────────────────────────────

output "aws_region" {
  value = var.aws_region
}

output "cognito_user_pool_id" {
  value = module.cognito.user_pool_id
}

output "cognito_user_pool_client_id" {
  value = module.cognito.user_pool_client_id
}

output "cognito_jwks_url" {
  value = module.cognito.jwks_url
}

output "s3_documents_bucket" {
  value = module.s3.bucket_name
}

output "rds_host" {
  value = module.rds.host
}

output "rds_port" {
  value = module.rds.port
}

output "rds_db_name" {
  value = module.rds.db_name
}

output "rds_db_user" {
  value = module.rds.db_username
}

output "rds_database_url" {
  value     = module.rds.database_url
  sensitive = true
}

output "sns_alerts_topic_arn" {
  value = module.sns.topic_arn
}

output "step_functions_state_machine_arn" {
  value = module.step_functions.state_machine_arn
}

output "lambda_function_name" {
  value = module.lambda.function_name
}
