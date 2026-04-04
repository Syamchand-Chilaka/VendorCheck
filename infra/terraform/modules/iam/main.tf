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

variable "sns_topic_arn" {
  type        = string
  description = "ARN of the SNS alerts topic"
}

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

# ── Lambda execution role ─────────────────────────────────

resource "aws_iam_role" "lambda" {
  name = "${var.project}-lambda-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })

  tags = {
    Project     = var.project
    Environment = var.environment
  }
}

# CloudWatch Logs
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# S3 read access for documents bucket
resource "aws_iam_role_policy" "lambda_s3" {
  name = "${var.project}-lambda-s3-${var.environment}"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:GetObject",
        "s3:HeadObject",
        "s3:PutObject",
      ]
      Resource = "${var.s3_bucket_arn}/*"
    }]
  })
}

# Step Functions start execution
resource "aws_iam_role_policy" "lambda_sfn" {
  name = "${var.project}-lambda-sfn-${var.environment}"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "states:StartExecution",
      ]
      Resource = "arn:aws:states:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:stateMachine:${var.project}-*"
    }]
  })
}

# ── Step Functions execution role ─────────────────────────

resource "aws_iam_role" "step_functions" {
  name = "${var.project}-sfn-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "states.amazonaws.com"
      }
    }]
  })

  tags = {
    Project     = var.project
    Environment = var.environment
  }
}

# Step Functions → Lambda invoke
resource "aws_iam_role_policy" "sfn_lambda" {
  name = "${var.project}-sfn-lambda-${var.environment}"
  role = aws_iam_role.step_functions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "lambda:InvokeFunction",
      ]
      Resource = "arn:aws:lambda:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:function:${var.project}-*"
    }]
  })
}

# Step Functions → SNS publish
resource "aws_iam_role_policy" "sfn_sns" {
  name = "${var.project}-sfn-sns-${var.environment}"
  role = aws_iam_role.step_functions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["sns:Publish"]
      Resource = var.sns_topic_arn
    }]
  })
}

# Step Functions → CloudWatch Logs
resource "aws_iam_role_policy" "sfn_logs" {
  name = "${var.project}-sfn-logs-${var.environment}"
  role = aws_iam_role.step_functions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "logs:CreateLogDelivery",
        "logs:GetLogDelivery",
        "logs:UpdateLogDelivery",
        "logs:DeleteLogDelivery",
        "logs:ListLogDeliveries",
        "logs:PutResourcePolicy",
        "logs:DescribeResourcePolicies",
        "logs:DescribeLogGroups",
      ]
      Resource = "*"
    }]
  })
}
