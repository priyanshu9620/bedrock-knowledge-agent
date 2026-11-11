variable "region" {
  default = "ap-southeast-2"
}
variable "profile" {
  default = "shopease"
}
variable "name" {
  default = "knowledge-agent"
}
variable "embedding_dimensions" {
  default = 768 # gemini-embedding-001 with output_dimensionality=768
}
variable "google_api_key" {
  sensitive = true
}
variable "api_token" {
  description = "shared secret the demo API requires in X-Api-Token"
  sensitive   = true
}
variable "gemini_model" {
  default = "gemini-3.5-flash-lite"
}
variable "embedding_model" {
  default = "gemini-embedding-001"
}
