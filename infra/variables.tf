variable "region" {
  default = "ap-southeast-2"
}
variable "profile" {
  default = "shopease"
}
variable "name" {
  default = "knowledge-agent"
}
variable "agent_model_profile" {
  description = "Inference profile id for the agent model (Nova 2 Lite needs the global profile in this account)"
  default     = "global.amazon.nova-2-lite-v1:0"
}
variable "agent_model_id" {
  description = "Foundation model id behind the profile (for the IAM policy)"
  default     = "amazon.nova-2-lite-v1:0"
}
variable "embedding_model_id" {
  default = "amazon.titan-embed-text-v2:0"
}
variable "embedding_dimensions" {
  default = 1024
}
