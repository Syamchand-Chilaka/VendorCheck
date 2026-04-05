output "function_arn" {
  value = aws_lambda_function.document_upload_handler.arn
}

output "function_name" {
  value = aws_lambda_function.document_upload_handler.function_name
}

output "log_group_name" {
  value = aws_cloudwatch_log_group.lambda.name
}
