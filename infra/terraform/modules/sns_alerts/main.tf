variable "project" {
  type        = string
  description = "Project name prefix for resource naming"
}

variable "environment" {
  type        = string
  description = "Environment name (dev, staging, prod)"
}

resource "aws_sns_topic" "alerts" {
  name = "${var.project}-alerts-${var.environment}"

  tags = {
    Project     = var.project
    Environment = var.environment
  }
}

# Dev: add an email subscription for testing
variable "alert_email" {
  type        = string
  default     = ""
  description = "Email address for alert notifications (optional, dev use)."
}

resource "aws_sns_topic_subscription" "email" {
  count     = var.alert_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}
