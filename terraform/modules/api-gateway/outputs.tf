output "api_id" {
  description = "API Gateway ID"
  value       = aws_apigatewayv2_api.main.id
}

output "api_url" {
  description = "API Gateway URL"
  value       = aws_apigatewayv2_api.main.api_endpoint
}

output "vpc_link_id" {
  description = "VPC Link ID"
  value       = aws_apigatewayv2_vpc_link.main.id
}
