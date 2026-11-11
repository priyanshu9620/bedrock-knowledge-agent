output "docs_bucket" { value = aws_s3_bucket.docs.bucket }
output "vector_bucket" { value = aws_s3vectors_vector_bucket.vectors.vector_bucket_name }
output "vector_index" { value = aws_s3vectors_index.handbook.index_name }
output "tools_lambda" { value = aws_lambda_function.tools.function_name }
output "api_lambda" { value = aws_lambda_function.api.function_name }
output "api_url" { value = aws_lambda_function_url.api.function_url }
