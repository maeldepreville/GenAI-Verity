variable "aws_region" {
  description = "La région AWS"
  type        = string
  default     = "eu-north-1"
}

variable "bucket_name" {
  description = "Le nom du bucket S3 d'ingestion"
  type        = string
}

variable "statement" {
    description = "Statement du trigger"
    type = string
}

variable "index_name" {
  description = "Nom de l'index de la collection"
  type        = string
}

variable "opensearch_host" {
  type    = string
}

variable "opensearch_endpoint" {
  type    = string
  description = "Endpoint de la collection"
}


variable "ecr_repo_url" {
    description = "Repository ECR"
    type = string
}

variable "lambda_image_tag" {
    description = "Tag image fonction lambda"
    type = string
    default = "latest" 
}

variable "google_api_key" {
    description = "Google API Key"
    type = string
    sensitive = true
}

variable "gemini_model" {
    description = "Google Gemini Model"
    type = string
    default = "gemini-1.5-pro"
}



