# Knowledge Agent v1 on the AWS Free plan — created by `make infra-apply`, removed by `make infra-destroy`.
#
#   corpus/*.md ─► S3 docs bucket ─► `ka ingest`: chunk → Gemini embeddings ─► Amazon S3 Vectors index (768-d, cosine)
#   question ─► agent (Gemini tool-calling loop) ─► retrieve_handbook (S3 Vectors query)  ─► cited answer
#                                └─► people-ops tools ─► Lambda `tools` (same handler a Bedrock action group would call)
#   public demo ─► Lambda `api` + Function URL (X-Api-Token) running the same agent code; Gemini key from SSM.
# Every resource has a one-line what/why. Free plan: no EC2/ALB, no Bedrock; everything here is free-tier or ₹0 idle.
# -----------------------------------------------------------------------------------------------------------------
provider "aws" {
  region  = var.region
  profile = var.profile
  default_tags {
    tags = { Project = "knowledge-agent", ManagedBy = "opentofu" }
  }
}

data "aws_caller_identity" "me" {}

locals {
  account      = data.aws_caller_identity.me.account_id
  corpus_files = fileset("${path.module}/../corpus", "*.md")
}

# ---- documents: private S3 bucket with corpus/*.md (what `ka ingest` reads) ----
resource "aws_s3_bucket" "docs" {
  bucket_prefix = "${var.name}-docs-"
  force_destroy = true
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

# ---- vector store: Amazon S3 Vectors — pay per request, nothing idle ----
resource "aws_s3vectors_vector_bucket" "vectors" {
  vector_bucket_name = "${var.name}-vectors-${local.account}"
}

resource "aws_s3vectors_index" "handbook" {
  vector_bucket_name = aws_s3vectors_vector_bucket.vectors.vector_bucket_name
  index_name         = "handbook"
  data_type          = "float32"
  dimension          = var.embedding_dimensions
  distance_metric    = "cosine"
  metadata_configuration {
    non_filterable_metadata_keys = ["text"] # chunk text rides along as metadata; only `doc` stays filterable
  }
}

# ---- secrets/config: SSM SecureString (free) read by the api Lambda at cold start ----
resource "aws_ssm_parameter" "google_api_key" {
  name  = "/${var.name}/GOOGLE_API_KEY"
  type  = "SecureString"
  value = var.google_api_key
}

resource "aws_ssm_parameter" "api_token" {
  name  = "/${var.name}/API_TOKEN"
  type  = "SecureString"
  value = var.api_token
}

# ---- tools Lambda: the four people-ops tools (zip from `make lambda-zip`) ----
resource "aws_iam_role" "tools" {
  name = "${var.name}-tools-lambda"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "lambda.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
}

resource "aws_iam_role_policy_attachment" "tools_logs" {
  role       = aws_iam_role.tools.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "tools" {
  function_name    = "${var.name}-tools"
  role             = aws_iam_role.tools.arn
  runtime          = "python3.12"
  handler          = "handler.lambda_handler"
  filename         = "${path.module}/../lambda/build/tools.zip"
  source_code_hash = filebase64sha256("${path.module}/../lambda/build/tools.zip")
  timeout          = 10
  memory_size      = 128
}

# ---- api Lambda: the agent behind a Function URL (same code as the CLI; deps bundled in api.zip) ----
resource "aws_iam_role" "api" {
  name = "${var.name}-api-lambda"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Effect = "Allow", Principal = { Service = "lambda.amazonaws.com" }, Action = "sts:AssumeRole" }]
  })
}

resource "aws_iam_role_policy_attachment" "api_logs" {
  role       = aws_iam_role.api.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "api" {
  name = "${var.name}-api"
  role = aws_iam_role.api.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      { Effect = "Allow", Action = ["s3vectors:QueryVectors", "s3vectors:GetVectors", "s3vectors:GetIndex"], Resource = [aws_s3vectors_index.handbook.index_arn, aws_s3vectors_vector_bucket.vectors.vector_bucket_arn] },
      { Effect = "Allow", Action = ["lambda:InvokeFunction"], Resource = aws_lambda_function.tools.arn },
      { Effect = "Allow", Action = ["ssm:GetParameter", "ssm:GetParameters"], Resource = [aws_ssm_parameter.google_api_key.arn, aws_ssm_parameter.api_token.arn] },
    ]
  })
}

resource "aws_lambda_function" "api" {
  function_name    = "${var.name}-api"
  role             = aws_iam_role.api.arn
  runtime          = "python3.12"
  handler          = "ka.lambda_api.handler"
  filename         = "${path.module}/../lambda/build/api.zip"
  source_code_hash = filebase64sha256("${path.module}/../lambda/build/api.zip")
  timeout          = 60
  memory_size      = 512
  environment {
    variables = {
      KA_NAME               = var.name
      KA_REGION             = var.region
      VECTOR_BUCKET         = aws_s3vectors_vector_bucket.vectors.vector_bucket_name
      VECTOR_INDEX          = aws_s3vectors_index.handbook.index_name
      TOOLS_LAMBDA          = aws_lambda_function.tools.function_name
      GEMINI_MODEL          = var.gemini_model
      GEMINI_FALLBACK_MODEL = var.gemini_fallback_model
      EMBEDDING_MODEL       = var.embedding_model
      EMBEDDING_DIMENSION   = tostring(var.embedding_dimensions)
    }
  }
}

resource "aws_lambda_function_url" "api" {
  function_name      = aws_lambda_function.api.function_name
  authorization_type = "NONE" # the function itself checks X-Api-Token (SSM); NONE keeps the demo page simple
  cors {
    allow_origins = ["*"]
    allow_methods = ["POST", "GET"]
    allow_headers = ["content-type", "x-api-token"]
  }
}

resource "aws_lambda_permission" "url" {
  statement_id           = "AllowFunctionUrl"
  action                 = "lambda:InvokeFunctionUrl"
  function_name          = aws_lambda_function.api.function_name
  principal              = "*"
  function_url_auth_type = "NONE"
}
