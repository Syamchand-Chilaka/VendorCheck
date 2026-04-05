variable "project" {
  type        = string
  description = "Project name prefix for resource naming"
}

variable "environment" {
  type        = string
  description = "Environment name (dev, staging, prod)"
}

variable "sns_topic_arn" {
  type        = string
  description = "SNS topic ARN for alert publishing"
}

# IMPORTANT: This state machine definition uses placeholder references
# (e.g. "#{OcrFunctionArn}") for Lambda functions that don't exist yet.
# The state machine will be created by Terraform, but executions will FAIL
# until you replace these placeholders with real Lambda function ARNs.
#
# When you create step-specific Lambda functions, replace the placeholder
# FunctionName values and re-apply.

resource "aws_sfn_state_machine" "document_pipeline" {
  name     = "${var.project}-doc-pipeline-${var.environment}"
  role_arn = var.sfn_role_arn

  definition = jsonencode({
    Comment = "VendorCheck document processing pipeline — placeholder Lambda ARNs, see module README"
    StartAt = "RunOCR"
    States = {
      RunOCR = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = "#{OcrFunctionArn}"
          Payload = {
            "tenant_id.$"            = "$.tenant_id"
            "document_id.$"          = "$.document_id"
            "document_version_id.$"  = "$.document_version_id"
            "vendor_id.$"            = "$.vendor_id"
            "bucket.$"               = "$.bucket"
            "key.$"                  = "$.key"
            "correlation_id.$"       = "$.correlation_id"
          }
        }
        ResultPath = "$.ocr_result"
        Retry = [{
          ErrorEquals     = ["States.TaskFailed", "Lambda.ServiceException"]
          IntervalSeconds = 5
          MaxAttempts     = 2
          BackoffRate     = 2.0
        }]
        Catch = [{
          ErrorEquals = ["States.ALL"]
          ResultPath  = "$.error"
          Next        = "PublishAlertOnFailure"
        }]
        Next = "StoreOCRArtifacts"
      }

      StoreOCRArtifacts = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = "#{StoreArtifactsFunctionArn}"
          Payload = {
            "tenant_id.$"            = "$.tenant_id"
            "document_id.$"          = "$.document_id"
            "document_version_id.$"  = "$.document_version_id"
            "bucket.$"               = "$.bucket"
            "ocr_result.$"           = "$.ocr_result"
            "correlation_id.$"       = "$.correlation_id"
          }
        }
        ResultPath = "$.store_result"
        Retry = [{
          ErrorEquals     = ["States.TaskFailed"]
          IntervalSeconds = 3
          MaxAttempts     = 2
          BackoffRate     = 2.0
        }]
        Catch = [{
          ErrorEquals = ["States.ALL"]
          ResultPath  = "$.error"
          Next        = "PublishAlertOnFailure"
        }]
        Next = "RunValidation"
      }

      RunValidation = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = "#{ValidationFunctionArn}"
          Payload = {
            "tenant_id.$"            = "$.tenant_id"
            "document_id.$"          = "$.document_id"
            "document_version_id.$"  = "$.document_version_id"
            "vendor_id.$"            = "$.vendor_id"
            "ocr_result.$"           = "$.ocr_result"
            "correlation_id.$"       = "$.correlation_id"
          }
        }
        ResultPath = "$.validation_result"
        Retry = [{
          ErrorEquals     = ["States.TaskFailed"]
          IntervalSeconds = 5
          MaxAttempts     = 2
          BackoffRate     = 2.0
        }]
        Catch = [{
          ErrorEquals = ["States.ALL"]
          ResultPath  = "$.error"
          Next        = "PublishAlertOnFailure"
        }]
        Next = "UpdateDocumentStatus"
      }

      UpdateDocumentStatus = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = "#{UpdateStatusFunctionArn}"
          Payload = {
            "tenant_id.$"            = "$.tenant_id"
            "document_id.$"          = "$.document_id"
            "document_version_id.$"  = "$.document_version_id"
            "validation_result.$"    = "$.validation_result"
            "correlation_id.$"       = "$.correlation_id"
          }
        }
        ResultPath = "$.status_update"
        Catch = [{
          ErrorEquals = ["States.ALL"]
          ResultPath  = "$.error"
          Next        = "PublishAlertOnFailure"
        }]
        Next = "RouteReviewOrApprove"
      }

      RouteReviewOrApprove = {
        Type = "Choice"
        Choices = [
          {
            Variable     = "$.validation_result.Payload.confidence"
            NumericLessThan = 0.8
            Next         = "CreateReviewTask"
          }
        ]
        Default = "AutoApprove"
      }

      CreateReviewTask = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = "#{CreateReviewFunctionArn}"
          Payload = {
            "tenant_id.$"            = "$.tenant_id"
            "document_id.$"          = "$.document_id"
            "document_version_id.$"  = "$.document_version_id"
            "vendor_id.$"            = "$.vendor_id"
            "validation_result.$"    = "$.validation_result"
            "correlation_id.$"       = "$.correlation_id"
          }
        }
        ResultPath = "$.review_task"
        Next       = "PublishReviewAlert"
      }

      PublishReviewAlert = {
        Type     = "Task"
        Resource = "arn:aws:states:::sns:publish"
        Parameters = {
          TopicArn = var.sns_topic_arn
          Message = {
            "event"                  = "review_task_created"
            "tenant_id.$"            = "$.tenant_id"
            "document_id.$"          = "$.document_id"
            "correlation_id.$"       = "$.correlation_id"
          }
        }
        ResultPath = "$.sns_result"
        Next       = "Done"
      }

      AutoApprove = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = "#{AutoApproveFunctionArn}"
          Payload = {
            "tenant_id.$"            = "$.tenant_id"
            "document_id.$"          = "$.document_id"
            "document_version_id.$"  = "$.document_version_id"
            "correlation_id.$"       = "$.correlation_id"
          }
        }
        ResultPath = "$.approve_result"
        Next       = "Done"
      }

      PublishAlertOnFailure = {
        Type     = "Task"
        Resource = "arn:aws:states:::sns:publish"
        Parameters = {
          TopicArn = var.sns_topic_arn
          Message = {
            "event"           = "pipeline_failure"
            "tenant_id.$"     = "$.tenant_id"
            "document_id.$"   = "$.document_id"
            "error.$"         = "$.error"
            "correlation_id.$" = "$.correlation_id"
          }
        }
        ResultPath = "$.sns_result"
        Next       = "Failed"
      }

      Failed = {
        Type = "Fail"
        Error = "PipelineFailure"
        Cause = "Document processing pipeline encountered an error"
      }

      Done = {
        Type = "Succeed"
      }
    }
  })

  tags = {
    Project     = var.project
    Environment = var.environment
  }
}

variable "sfn_role_arn" {
  type        = string
  description = "IAM role ARN for the Step Functions state machine"
}
