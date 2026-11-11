output "knowledge_base_id" { value = aws_bedrockagent_knowledge_base.kb.id }
output "data_source_id" { value = aws_bedrockagent_data_source.docs.data_source_id }
output "agent_id" { value = aws_bedrockagent_agent.agent.agent_id }
output "agent_alias_id" { value = aws_bedrockagent_agent_alias.live.agent_alias_id }
output "docs_bucket" { value = aws_s3_bucket.docs.bucket }
output "vector_bucket" { value = aws_s3vectors_vector_bucket.vectors.vector_bucket_name }
output "lambda_function" { value = aws_lambda_function.tools.function_name }
