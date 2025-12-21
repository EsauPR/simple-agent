variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "kavak-agent"
}

variable "environment" {
  description = "Environment name (e.g., production, staging)"
  type        = string
  default     = "production"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "ecs_desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 2
}

variable "ecs_min_capacity" {
  description = "Minimum number of ECS tasks for auto scaling"
  type        = number
  default     = 1
}

variable "ecs_max_capacity" {
  description = "Maximum number of ECS tasks for auto scaling"
  type        = number
  default     = 10
}

variable "ec2_instance_type" {
  description = "EC2 instance type for ECS"
  type        = string
  default     = "t3.medium"
}

variable "aurora_instance_class" {
  description = "Aurora instance class"
  type        = string
  default     = "db.serverless"
}

variable "aurora_min_capacity" {
  description = "Minimum Aurora Serverless v2 capacity (ACUs)"
  type        = number
  default     = 0.5
}

variable "aurora_max_capacity" {
  description = "Maximum Aurora Serverless v2 capacity (ACUs)"
  type        = number
  default     = 16
}

variable "db_name" {
  description = "Name of the database"
  type        = string
  default     = "kavak_db"
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "kavak_user"
  sensitive   = true
}

variable "bastion_allowed_ip_cidr" {
  description = "CIDR block of IP allowed to SSH to bastion (e.g., 189.250.78.17/32)"
  type        = string
  default     = ""
}

variable "bastion_key_pair_name" {
  description = "Name of AWS Key Pair for bastion host SSH access (optional)"
  type        = string
  default     = ""
}
