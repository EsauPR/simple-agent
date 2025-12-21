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

variable "db_security_group_id" {
  description = "Database security group ID"
  type        = string
}

variable "db_name" {
  description = "Name of the database"
  type        = string
}

variable "db_username" {
  description = "Database master username"
  type        = string
  sensitive   = true
}

variable "db_password_secret_arn" {
  description = "ARN of the secret containing the database password"
  type        = string
}

variable "aurora_instance_class" {
  description = "Aurora instance class"
  type        = string
}

variable "aurora_min_capacity" {
  description = "Minimum Aurora Serverless v2 capacity (ACUs)"
  type        = number
}

variable "aurora_max_capacity" {
  description = "Maximum Aurora Serverless v2 capacity (ACUs)"
  type        = number
}
