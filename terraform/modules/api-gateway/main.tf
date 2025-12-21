# API Gateway REST API
resource "aws_apigatewayv2_api" "main" {
  name          = "${var.project_name}-${var.environment}-api"
  protocol_type = "HTTP"
  description   = "API Gateway for ${var.project_name}"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["*"]
    allow_headers = ["*"]
    max_age       = 300
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-api"
  }
}

# VPC Link V2
resource "aws_apigatewayv2_vpc_link" "main" {
  name               = "${var.project_name}-${var.environment}-vpc-link"
  security_group_ids = [aws_security_group.vpc_link.id]
  subnet_ids         = var.private_subnet_ids

  tags = {
    Name = "${var.project_name}-${var.environment}-vpc-link"
  }

  # VPC Link V2 requires at least 2 subnets in different AZs
  depends_on = [aws_security_group.vpc_link]
}

# Security Group for VPC Link
resource "aws_security_group" "vpc_link" {
  name        = "${var.project_name}-${var.environment}-vpc-link-sg"
  description = "Security group for API Gateway VPC Link"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTPS from API Gateway VPC Link"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    description = "HTTP to ALB"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-vpc-link-sg"
  }
}

# Integration for all routes
resource "aws_apigatewayv2_integration" "alb" {
  api_id = aws_apigatewayv2_api.main.id

  integration_type   = "HTTP_PROXY"
  integration_method = "ANY"
  integration_uri    = var.alb_listener_arn
  connection_type    = "VPC_LINK"
  connection_id      = aws_apigatewayv2_vpc_link.main.id

  payload_format_version = "1.0"
}

# Default route (catch-all for HTTP API)
resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.alb.id}"
}

# Stage
resource "aws_apigatewayv2_stage" "production" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip            = "$context.identity.sourceIp"
      requestTime   = "$context.requestTime"
      httpMethod    = "$context.httpMethod"
      routeKey      = "$context.routeKey"
      status        = "$context.status"
      protocol      = "$context.protocol"
      responseLength = "$context.responseLength"
    })
  }

  default_route_settings {
    throttling_burst_limit = 100
    throttling_rate_limit  = 50
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-api-stage"
  }
}

# CloudWatch Log Group for API Gateway
resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/${var.project_name}-${var.environment}"
  retention_in_days = 7

  tags = {
    Name = "${var.project_name}-${var.environment}-api-logs"
  }
}
