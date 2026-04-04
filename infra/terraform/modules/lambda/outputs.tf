output "function_arn" {
  value = aws_lambda_function.document_upload_handler.arn
}

output "function_name" {
  value = aws_lambda_function.document_upload_handler.function_name
}
