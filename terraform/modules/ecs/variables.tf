variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs"
  type        = list(string)
}

variable "ecs_security_group_id" {
  description = "ECS security group ID"
  type        = string
}

variable "ecr_repository_url" {
  description = "ECR repository URL"
  type        = string
}

variable "ecs_task_role_arn" {
  description = "ECS task role ARN"
  type        = string
}

variable "ecs_execution_role_arn" {
  description = "ECS execution role ARN"
  type        = string
}

variable "ec2_instance_type" {
  description = "EC2 instance type"
  type        = string
}

variable "ecs_desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
}

variable "ecs_min_capacity" {
  description = "Minimum number of ECS tasks"
  type        = number
}

variable "ecs_max_capacity" {
  description = "Maximum number of ECS tasks"
  type        = number
}

variable "database_url_secret_arn" {
  description = "Database URL secret ARN"
  type        = string
}

variable "openai_api_key_secret_arn" {
  description = "OpenAI API key secret ARN"
  type        = string
}

variable "twilio_secrets_arn" {
  description = "Twilio secrets ARN"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "target_group_arn" {
  description = "Target group ARN for load balancer"
  type        = string
}
