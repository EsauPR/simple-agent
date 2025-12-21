output "alb_security_group_id" {
  description = "ALB security group ID"
  value       = aws_security_group.alb.id
}

output "ecs_security_group_id" {
  description = "ECS security group ID"
  value       = aws_security_group.ecs.id
}

output "db_security_group_id" {
  description = "Database security group ID"
  value       = aws_security_group.db.id
}

output "ecs_execution_role_arn" {
  description = "ECS task execution role ARN"
  value       = aws_iam_role.ecs_execution.arn
}

output "ecs_task_role_arn" {
  description = "ECS task role ARN"
  value       = aws_iam_role.ecs_task.arn
}

output "database_url_secret_arn" {
  description = "Database URL secret ARN"
  value       = aws_secretsmanager_secret.database_url.arn
}

output "openai_api_key_secret_arn" {
  description = "OpenAI API key secret ARN"
  value       = aws_secretsmanager_secret.openai_api_key.arn
}

output "twilio_secrets_arn" {
  description = "Twilio secrets ARN"
  value       = aws_secretsmanager_secret.twilio.arn
}

output "cognito_secrets_arn" {
  description = "Cognito secrets ARN"
  value       = aws_secretsmanager_secret.cognito.arn
}

output "db_password_secret_arn" {
  description = "Database password secret ARN"
  value       = aws_secretsmanager_secret.db_password.arn
}

output "db_password" {
  description = "Database password (from secret)"
  value       = random_password.db_password.result
  sensitive   = true
}
