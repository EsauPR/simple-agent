output "api_gateway_url" {
  description = "API Gateway URL"
  value       = module.api_gateway.api_url
}

output "aurora_endpoint" {
  description = "Aurora cluster endpoint"
  value       = module.aurora.cluster_endpoint
  sensitive   = true
}

output "aurora_reader_endpoint" {
  description = "Aurora cluster reader endpoint"
  value       = module.aurora.cluster_reader_endpoint
  sensitive   = true
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.ecs.cluster_name
}

output "ecs_service_name" {
  description = "ECS service name"
  value       = module.ecs.service_name
}

output "alb_dns_name" {
  description = "ALB DNS name (internal)"
  value       = module.alb.alb_dns_name
}

output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.app.repository_url
}

output "ecr_repository_name" {
  description = "ECR repository name"
  value       = aws_ecr_repository.app.name
}

output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "bastion_public_ip" {
  description = "Bastion host public IP address"
  value       = module.bastion.bastion_public_ip
}

output "bastion_public_dns" {
  description = "Bastion host public DNS name"
  value       = module.bastion.bastion_public_dns
}
