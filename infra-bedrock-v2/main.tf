# Bedrock Knowledge Agent on AWS — everything here is created by `make infra-apply` and removed by `make infra-destroy`.
#
#   corpus/*.md ──► S3 docs bucket ──► Knowledge Base (Titan Embeddings v2) ──► S3 Vectors index (no idle cost)
#                                            ▲
#   user ──► Bedrock Agent (Nova 2 Lite) ────┤ Retrieve (citations)
#                      │
#                      └──► action group "people-ops" (OpenAPI) ──► Lambda (4 tools over data.json)
#
# Each resource has a one-line what/why. Region/account: the free-plan project (SCP-limited to ap-southeast-2).
# ---------------------------------------------------------------------------------------------------------------
provider "aws" {
  region  = var.region
  profile = var.profile
  default_tags {
    tags = { Project = "bedrock-knowledge-agent", ManagedBy = "opentofu" }
  }
}

data "aws_caller_identity" "me" {}

locals {
  account      = data.aws_caller_identity.me.account_id
  embed_arn    = "arn:aws:bedrock:${var.region}::foundation-model/${var.embedding_model_id}"
  profile_arn  = "arn:aws:bedrock:${var.region}:${local.account}:inference-profile/${var.agent_model_profile}"
  fm_any_arn   = "arn:aws:bedrock:*::foundation-model/${var.agent_model_id}" # a global profile routes to other regions
  corpus_files = fileset("${path.module}/../corpus", "*.md")
}

# ---- documents: a private S3 bucket holding corpus/*.md (the Knowledge Base's data source) ----
resource "aws_s3_bucket" "docs" {
  bucket_prefix = "${var.name}-docs-"
  force_destroy = true # destroy removes the objects too
}

resource "aws_s3_bucket_public_access_block" "docs" {
  bucket                  = aws_s3_bucket.docs.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_object" "corpus" {
  for_each     = local.corpus_files
  bucket       = aws_s3_bucket.docs.id
  key          = "handbook/${each.value}"
  source       = "${path.module}/../corpus/${each.value}"
  etag         = filemd5("${path.module}/../corpus/${each.value}")
  content_type = "text/markdown"
}

# ---- vector store: S3 Vectors (pay per use; OpenSearch Serverless would bill ≥2 OCUs/hour from creation) ----
resource "aws_s3vectors_vector_bucket" "vectors" {
  vector_bucket_name = "${var.name}-vectors-${local.account}"
}

resource "aws_s3vectors_index" "kb" {
  vector_bucket_name = aws_s3vectors_vector_bucket.vectors.vector_bucket_name
  index_name         = "handbook"
  data_type          = "float32"
  dimension          = var.embedding_dimensions
  distance_metric    = "cosine"
  metadata_configuration {
    # Bedrock stores the chunk text + its metadata as vector metadata; these must be non-filterable (size limits)
    non_filterable_metadata_keys = ["AMAZON_BEDROCK_TEXT", "AMAZON_BEDROCK_METADATA"]
  }
}

# ---- Knowledge Base role: read the docs bucket, call the embedding model, read/write the vector index ----
resource "aws_iam_role" "kb" {
  name = "${var.name}-kb"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "bedrock.amazonaws.com" }
      Action    = "sts:AssumeRole"
      Condition = { StringEquals = { "aws:SourceAccount" = local.account } }
    }]
  })
}

resource "aws_iam_role_policy" "kb" {
  name = "${var.name}-kb"
  role = aws_iam_role.kb.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = ["bedrock:InvokeModel"], Resource = local.embed_arn },
      { Effect = "Allow", Action = ["s3:ListBucket"], Resource = aws_s3_bucket.docs.arn, Condition = { StringEquals = { "aws:ResourceAccount" = local.account } } },
      { Effect = "Allow", Action = ["s3:GetObject"], Resource = "${aws_s3_bucket.docs.arn}/*", Condition = { StringEquals = { "aws:ResourceAccount" = local.account } } },
      { Effect = "Allow", Action = ["s3vectors:*"], Resource = [aws_s3vectors_vector_bucket.vectors.vector_bucket_arn, aws_s3vectors_index.kb.index_arn] },
    ]
  })
}

# ---- Knowledge Base + S3 data source ----
resource "aws_bedrockagent_knowledge_base" "kb" {
  name     = "${var.name}-handbook"
  role_arn = aws_iam_role.kb.arn
  knowledge_base_configuration {
    type = "VECTOR"
    vector_knowledge_base_configuration {
      embedding_model_arn = local.embed_arn
      embedding_model_configuration {
        bedrock_embedding_model_configuration {
          dimensions          = var.embedding_dimensions
          embedding_data_type = "FLOAT32"
        }
      }
    }
  }
  storage_configuration {
    type = "S3_VECTORS"
    s3_vectors_configuration {
      index_arn = aws_s3vectors_index.kb.index_arn
    }
  }
  depends_on = [aws_iam_role_policy.kb]
}

resource "aws_bedrockagent_data_source" "docs" {
  knowledge_base_id = aws_bedrockagent_knowledge_base.kb.id
  name              = "handbook-s3"
  data_source_configuration {
    type = "S3"
    s3_configuration {
      bucket_arn         = aws_s3_bucket.docs.arn
      inclusion_prefixes = ["handbook/"]
    }
  }
  vector_ingestion_configuration {
    chunking_configuration {
      chunking_strategy = "FIXED_SIZE"
      fixed_size_chunking_configuration {
        max_tokens         = 300
        overlap_percentage = 20
      }
    }
  }
}

# ---- Lambda: the four tools (zip built by `make lambda-zip`) ----
resource "aws_iam_role" "lambda" {
  name = "${var.name}-tools-lambda"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "lambda.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "tools" {
  function_name    = "${var.name}-tools"
  role             = aws_iam_role.lambda.arn
  runtime          = "python3.12"
  handler          = "handler.lambda_handler"
  filename         = "${path.module}/../lambda/build/tools.zip"
  source_code_hash = filebase64sha256("${path.module}/../lambda/build/tools.zip")
  timeout          = 10
  memory_size      = 128
}

resource "aws_lambda_permission" "bedrock" {
  statement_id  = "AllowBedrockAgent"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.tools.function_name
  principal     = "bedrock.amazonaws.com"
  source_arn    = aws_bedrockagent_agent.agent.agent_arn
}

# ---- Agent role: invoke the model (via the global inference profile), retrieve from the KB ----
resource "aws_iam_role" "agent" {
  name = "${var.name}-agent"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "bedrock.amazonaws.com" }
      Action    = "sts:AssumeRole"
      Condition = { StringEquals = { "aws:SourceAccount" = local.account } }
    }]
  })
}

resource "aws_iam_role_policy" "agent" {
  name = "${var.name}-agent"
  role = aws_iam_role.agent.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream", "bedrock:GetInferenceProfile"], Resource = [local.profile_arn, local.fm_any_arn] },
      { Effect = "Allow", Action = ["bedrock:Retrieve"], Resource = aws_bedrockagent_knowledge_base.kb.arn },
    ]
  })
}

# ---- the Agent, its action group (OpenAPI → Lambda), the KB association, and an alias to call ----
resource "aws_bedrockagent_agent" "agent" {
  agent_name                  = var.name
  agent_resource_role_arn     = aws_iam_role.agent.arn
  foundation_model            = local.profile_arn
  idle_session_ttl_in_seconds = 600
  prepare_agent               = true
  instruction                 = file("${path.module}/instruction.txt")
  depends_on                  = [aws_iam_role_policy.agent]
}

resource "aws_bedrockagent_agent_action_group" "people_ops" {
  agent_id                   = aws_bedrockagent_agent.agent.agent_id
  agent_version              = "DRAFT"
  action_group_name          = "people-ops"
  description                = "Live people-ops data: leave balance, reimbursement, holidays, helpdesk tickets"
  skip_resource_in_use_check = true
  action_group_executor {
    lambda = aws_lambda_function.tools.arn
  }
  api_schema {
    payload = file("${path.module}/../lambda/openapi.yml")
  }
}

resource "aws_bedrockagent_agent_knowledge_base_association" "kb" {
  agent_id             = aws_bedrockagent_agent.agent.agent_id
  agent_version        = "DRAFT"
  knowledge_base_id    = aws_bedrockagent_knowledge_base.kb.id
  knowledge_base_state = "ENABLED"
  description          = "Meridian Labs employee handbook: leave, expenses, travel, IT security, onboarding, devices, remote work, holidays, benefits, conduct, incidents, glossary"
}

resource "aws_bedrockagent_agent_alias" "live" {
  agent_id         = aws_bedrockagent_agent.agent.agent_id
  agent_alias_name = "live"
  description      = "alias used by the CLI, the demo page and the evaluation"
  depends_on       = [aws_bedrockagent_agent_action_group.people_ops, aws_bedrockagent_agent_knowledge_base_association.kb]
}
