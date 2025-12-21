provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# ECR Repository
resource "aws_ecr_repository" "app" {
  name                 = "${var.project_name}-${var.environment}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }
}

resource "aws_ecr_lifecycle_policy" "app" {
  repository = aws_ecr_repository.app.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 10 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"

  project_name = var.project_name
  environment  = var.environment
  vpc_cidr     = var.vpc_cidr
  azs          = slice(data.aws_availability_zones.available.names, 0, 2)
}

# Bastion Host Module (for database access)
module "bastion" {
  source = "./modules/bastion"

  project_name     = var.project_name
  environment      = var.environment
  vpc_id           = module.vpc.vpc_id
  public_subnet_ids = module.vpc.public_subnet_ids
  allowed_ip_cidr  = var.bastion_allowed_ip_cidr
  key_pair_name    = var.bastion_key_pair_name

  depends_on = [
    module.vpc
  ]
}

# Security Module
module "security" {
  source = "./modules/security"

  project_name        = var.project_name
  environment         = var.environment
  vpc_id              = module.vpc.vpc_id
  vpc_cidr            = var.vpc_cidr
  aws_account_id      = data.aws_caller_identity.current.account_id
  aws_region          = var.aws_region
  ecr_repository_arn  = aws_ecr_repository.app.arn
  ecr_repository_url  = aws_ecr_repository.app.repository_url
  bastion_security_group_id = module.bastion.bastion_security_group_id

  depends_on = [
    aws_ecr_repository.app,
    module.vpc,
    module.bastion
  ]
}

# Aurora Module
module "aurora" {
  source = "./modules/aurora"

  project_name           = var.project_name
  environment            = var.environment
  vpc_id                 = module.vpc.vpc_id
  private_subnet_ids     = module.vpc.private_subnet_ids
  db_security_group_id   = module.security.db_security_group_id
  db_name                = var.db_name
  db_username            = var.db_username
  db_password_secret_arn = module.security.db_password_secret_arn
  aurora_instance_class  = var.aurora_instance_class
  aurora_min_capacity    = var.aurora_min_capacity
  aurora_max_capacity    = var.aurora_max_capacity

  depends_on = [
    module.vpc,
    module.security
  ]
}

# ALB Module (created before ECS to provide target group)
module "alb" {
  source = "./modules/alb"

  project_name          = var.project_name
  environment           = var.environment
  vpc_id                = module.vpc.vpc_id
  private_subnet_ids    = module.vpc.private_subnet_ids
  alb_security_group_id = module.security.alb_security_group_id
  ecs_service_name      = "${var.project_name}-${var.environment}-service"
  ecs_cluster_name      = "${var.project_name}-${var.environment}-cluster"

  depends_on = [
    module.vpc,
    module.security
  ]
}

# Get database password from secret
data "aws_secretsmanager_secret_version" "db_password" {
  secret_id  = module.security.db_password_secret_arn
  depends_on = [module.security]
}

# Update Database URL secret after Aurora is created
# Note: We need to URL-encode the password to handle special characters
resource "aws_secretsmanager_secret_version" "database_url" {
  secret_id = module.security.database_url_secret_arn
  secret_string = "postgresql+asyncpg://${var.db_username}:${urlencode(data.aws_secretsmanager_secret_version.db_password.secret_string)}@${module.aurora.cluster_endpoint}:5432/${var.db_name}"

  lifecycle {
    ignore_changes = [secret_string]
  }

  depends_on = [
    module.aurora,
    data.aws_secretsmanager_secret_version.db_password
  ]
}

# ECS Module
module "ecs" {
  source = "./modules/ecs"

  project_name              = var.project_name
  environment               = var.environment
  vpc_id                    = module.vpc.vpc_id
  private_subnet_ids        = module.vpc.private_subnet_ids
  ecs_security_group_id     = module.security.ecs_security_group_id
  ecr_repository_url        = aws_ecr_repository.app.repository_url
  ecs_task_role_arn         = module.security.ecs_task_role_arn
  ecs_execution_role_arn    = module.security.ecs_execution_role_arn
  ec2_instance_type         = var.ec2_instance_type
  ecs_desired_count         = var.ecs_desired_count
  ecs_min_capacity          = var.ecs_min_capacity
  ecs_max_capacity          = var.ecs_max_capacity
  database_url_secret_arn   = module.security.database_url_secret_arn
  openai_api_key_secret_arn = module.security.openai_api_key_secret_arn
  twilio_secrets_arn        = module.security.twilio_secrets_arn
  cognito_secrets_arn       = module.security.cognito_secrets_arn
  aws_region                = var.aws_region
  target_group_arn          = module.alb.target_group_arn

  depends_on = [
    module.vpc,
    module.security,
    module.aurora,
    module.alb,
    aws_ecr_repository.app,
    aws_secretsmanager_secret_version.database_url
  ]
}

# API Gateway Module
module "api_gateway" {
  source = "./modules/api-gateway"

  project_name       = var.project_name
  environment        = var.environment
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  alb_arn            = module.alb.alb_arn
  alb_dns_name       = module.alb.alb_dns_name
  alb_listener_arn   = module.alb.listener_arn
  aws_region         = var.aws_region
  vpc_cidr           = var.vpc_cidr

  depends_on = [
    module.vpc,
    module.alb
  ]
}
