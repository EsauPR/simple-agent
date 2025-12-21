output "cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "cluster_id" {
  description = "ECS cluster ID"
  value       = aws_ecs_cluster.main.id
}

output "service_name" {
  description = "ECS service name"
  value       = aws_ecs_service.app.name
}

output "service_id" {
  description = "ECS service ID"
  value       = aws_ecs_service.app.id
}

output "task_definition_arn" {
  description = "Task definition ARN"
  value       = aws_ecs_task_definition.app.arn
}
