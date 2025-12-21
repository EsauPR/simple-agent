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

variable "public_subnet_ids" {
  description = "List of public subnet IDs"
  type        = list(string)
}

variable "allowed_ip_cidr" {
  description = "CIDR block of allowed IP for SSH access (e.g., 189.250.78.17/32)"
  type        = string
}

variable "key_pair_name" {
  description = "Name of existing AWS Key Pair for SSH access (optional)"
  type        = string
  default     = ""
}
