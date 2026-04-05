variable "project" {
  type        = string
  description = "Project name prefix for resource naming"
}

variable "environment" {
  type        = string
  description = "Environment name (dev, staging, prod)"
}

variable "s3_bucket_arn" {
  type        = string
  description = "ARN of the S3 documents bucket"
}

variable "s3_bucket_name" {
  type        = string
  description = "Name of the S3 documents bucket"
}

variable "rds_database_url" {
  type        = string
  sensitive   = true
  description = "PostgreSQL connection URL"
}

variable "step_functions_arn" {
  type        = string
  description = "ARN of the Step Functions state machine"
}

variable "lambda_role_arn" {
  type        = string
  description = "IAM role ARN for the Lambda function"
}

data "archive_file" "handler" {
  type        = "zip"
  source_dir  = "${path.module}/src"
  output_path = "${path.module}/handler.zip"
}

# Explicit log group with retention — avoids unbounded CloudWatch costs
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.project}-doc-upload-handler-${var.environment}"
  retention_in_days = 30

  tags = {
    Project     = var.project
    Environment = var.environment
  }
}

resource "aws_lambda_function" "document_upload_handler" {
  function_name = "${var.project}-doc-upload-handler-${var.environment}"
  role          = var.lambda_role_arn
  handler       = "handler.lambda_handler"
  runtime       = "python3.11"
  timeout       = 30
  memory_size   = 256

  filename         = data.archive_file.handler.output_path
  source_code_hash = data.archive_file.handler.output_base64sha256

  environment {
    variables = {
      S3_DOCUMENTS_BUCKET        = var.s3_bucket_name
      DATABASE_URL               = var.rds_database_url
      STATE_MACHINE_ARN          = var.step_functions_arn
      ENVIRONMENT                = var.environment
    }
  }

  tags = {
    Project     = var.project
    Environment = var.environment
  }

  depends_on = [aws_cloudwatch_log_group.lambda]
}

# Allow S3 to invoke this Lambda
resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.document_upload_handler.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = var.s3_bucket_arn
}
