#-----------------------------
#         PROVIDERS
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
  region = var.aws_region
}


#-----------------------------
#         LOCALS ARN
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
#         RESOURCES
#-----------------------------

# OpenSearch

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

resource "aws_s3_bucket" "module_ingestion" {
  bucket = var.bucket_name
}



# Bucket settings
resource "aws_s3_bucket_public_access_block" "regulations_access" {
  bucket                  = aws_s3_bucket.module_ingestion.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lambda

# Fonction Lambda pour l'ingestion

resource "aws_lambda_function" "function" {
  function_name = "trigger-g1-mg01"

  role    = "arn:aws:iam::073184925698:role/service-role/trigger-g1-mg01-role-ek0d14u2"
  package_type = "Image"
  image_uri    = "${var.ecr_repo_url}:${var.lambda_image_tag}"
  tags         = {}
  timeout      = 120
  memory_size  = 128

  environment {
    variables = {
      GOOGLE_API_KEY      = var.google_api_key
      OPENSEARCH_HOST     = var.opensearch_host
      OPENSEARCH_REGION   = var.aws_region
      GEMINI_MODEL        = var.gemini_model

    }
  }

}


# Permission pour S3 d'appeler la Lambda
resource "aws_lambda_permission" "allow_s3" {
  statement_id  = var.statement
  source_account = "073184925698"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.function.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.module_ingestion.arn
}


resource "aws_s3_bucket_notification" "trigger_lambda" {
  bucket = aws_s3_bucket.module_ingestion.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.function.arn
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = ".txt"
  }

  depends_on = [aws_lambda_permission.allow_s3]
}

#-----------------------------
#           IAM
#-----------------------------

# Rôle IAM de Lambda - Trust Policy
resource "aws_iam_role" "iam_lambda" {
  name = "trigger-g1-mg01-role-ek0d14u2"
  path = "/service-role/"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# Managed policies (by AWS) for Lambda
resource "aws_iam_role_policy_attachment" "maccess_lambda_ingestion_full" {
  role       = aws_iam_role.iam_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonOpenSearchIngestionFullAccess"
}

resource "aws_iam_role_policy_attachment" "maccess_lambda_ingestion_read" {
  role       = aws_iam_role.iam_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonOpenSearchIngestionReadOnlyAccess"
}

resource "aws_iam_role_policy_attachment" "maccess_lambda_opensearch" {
  role       = aws_iam_role.iam_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonOpenSearchServiceFullAccess"
}

resource "aws_iam_role_policy_attachment" "maccess_lambda_s3" {
  role       = aws_iam_role.iam_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

# CloudWatch
resource "aws_iam_role_policy_attachment" "maccess_lambda_cwatch" {
  role       = aws_iam_role.iam_lambda.name
  policy_arn = "arn:aws:iam::073184925698:policy/service-role/AWSLambdaBasicExecutionRole-59280565-44f0-4e7d-97c2-15b1c41e6650"
}

# Inline policies content
data "aws_iam_policy_document" "ip_ecr" {
  statement {
    effect = "Allow"

    actions = [
      "ecr:GetAuthorizationToken",
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "ecr:PutImage",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload"
    ]

    resources = ["*"]
  }
}


data "aws_iam_policy_document" "ip_opensearch" {
  statement {
    effect = "Allow"

    actions = [
				"aoss:ListCollections",
				"aoss:BatchGetCollection",
				"aoss:APIAccessAll"
    ]

    resources = ["*"]
  }
}

# Applying Inline policies
resource "aws_iam_role_policy" "ip_ecr" {
  name   = "IP-ECR-G1GM01"
  role   = aws_iam_role.iam_lambda.name
  policy = data.aws_iam_policy_document.ip_ecr.json
}

resource "aws_iam_role_policy" "ip_opensearch" {
  name   = "IP-OpenSearch-G1MG01"
  role   = aws_iam_role.iam_lambda.name
  policy = data.aws_iam_policy_document.ip_opensearch.json
}