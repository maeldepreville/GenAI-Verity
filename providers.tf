#-----------------------------
#         CONFIGURATION
#-----------------------------
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "eu-north-1"
}


#-----------------------------
#         PARAMETERS
#-----------------------------


# On définit la liste des ARNs autorisés pour plus de clarté

locals {
  authorized_principals = [
    "arn:aws:iam::073184925698:role/aws-reserved/sso.amazonaws.com/eu-west-3/AWSReservedSSO_MLOps-Students_ac9a3e563f1c05f7",
    "arn:aws:iam::073184925698:user/git-user-g1mg01",
    "arn:aws:iam::073184925698:role/service-role/trigger-g1-mg01-role-ek0d14u2"
  ]
}



#-----------------------------
#         RESSOURCES
#-----------------------------

# OpenSearch

# Collection
resource "aws_opensearchserverless_collection" "collection" {
  name       = "compliance-vectors"
  type       = "VECTORSEARCH"
  description = "Verity project collection (GRP1-01)"
}

# On ne définit pas la création de l'index car mal-géré par Terraform
# Présence de l'index à vérifier à travers le code, sa structure est à retrouver dans config/index-gemini.json

# Data Access Policy
resource "aws_opensearchserverless_access_policy" "data_policy" {
  name        = "easy-compliance-vectors"
  type        = "data"
  description = "Stratégie en matière de données simplifiée"
  policy = jsonencode([
    {
      Rules = [
        {
          ResourceType = "collection"
          Resource     = ["collection/compliance-vectors"]
          Permission   = [
            "aoss:CreateCollectionItems",
            "aoss:DeleteCollectionItems",
            "aoss:UpdateCollectionItems",
            "aoss:DescribeCollectionItems"
          ]
        },
        {
          ResourceType = "index"
          Resource     = ["index/compliance-vectors/*"]
          Permission   = [
            "aoss:CreateIndex",
            "aoss:DeleteIndex",
            "aoss:UpdateIndex",
            "aoss:DescribeIndex",
            "aoss:ReadDocument",
            "aoss:WriteDocument"
          ]
        }
      ],
      Principal = local.authorized_principals # Utilisation de notre liste définie plus haut
    }
  ])
}


# S3

# Bucket
resource "aws_s3_bucket" "module_ingestion" {
  bucket = "S3-g1mg01"
  force_destroy = true # Permet de supprimer le bucket même s'il contient des fichiers
}

############### IMPORT NON-FAIT 

# Blocage de l'accès public (Sécurité)
resource "aws_s3_bucket_public_access_block" "regulations_access" {
  bucket                  = aws_s3_bucket.module_ingestion.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# Lambda

# Fonction Lambda pour l'ingestion
resource "aws_lambda_function" "module_ingestion" {
  filename      = "lambda_function_payload.zip"
  function_name = "lambda_function"
  role          = aws_iam_role.lambda_exec_role.arn
  handler       = "ingestion.lambda_handler" # Le point d'entrée de ton script
  runtime       = "python3.9"
  timeout       = 300 # 5 minutes pour gérer les gros fichiers
  memory_size   = 512

  # Injection des variables d'environnement cruciales
  environment {
    variables = {
      GOOGLE_API_KEY      = var.google_api_key
      OPENSEARCH_ENDPOINT = aws_opensearchserverless_collection.compliance_vectors.kms_key_arn
      INDEX_NAME          = "index-gemini"
    }
  }
}

resource "aws_s3_bucket_notification" "trigger_lambda" {
  bucket = aws_s3_bucket.module_ingestion.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = ".txt"
  }

  depends_on = [aws_lambda_permission.allow_s3]
}

# Permission pour S3 d'appeler la Lambda
resource "aws_lambda_permission" "allow_s3" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ingestion_worker.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.regulations_bucket.arn
}


# 3. Politique IAM pour autoriser ton Agent à appeler Claude 3.5 sur Bedrock
resource "aws_iam_policy" "bedrock_invoke" {
  name        = "ComplianceAgentBedrockAccess"
  description = "Permet l'invocation de Claude 3.5 Sonnet"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = "bedrock:InvokeModel"
        Effect   = "Allow"
        Resource = "arn:aws:bedrock:eu-north-1::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0"
      }
    ]
  })
}