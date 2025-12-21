# DB Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-${var.environment}-db-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name = "${var.project_name}-${var.environment}-db-subnet-group"
  }
}

# Parameter Group for pgvector
resource "aws_rds_cluster_parameter_group" "pgvector" {
  name        = "${var.project_name}-${var.environment}-pgvector-params-v16"
  family      = "aurora-postgresql16"
  description = "Parameter group for Aurora PostgreSQL 16 with pgvector"

  # shared_preload_libraries is a static parameter that requires a reboot
  # For cluster parameter groups, parameters are applied on next reboot automatically
  parameter {
    name  = "shared_preload_libraries"
    value = "vector"
  }

  parameter {
    name  = "max_connections"
    value = "100"
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-pgvector-params"
  }

  lifecycle {
    create_before_destroy = true
    ignore_changes = [
      # Ignore changes to parameters if they're modified outside Terraform
      parameter
    ]
  }
}

# Get database password from Secrets Manager
data "aws_secretsmanager_secret_version" "db_password" {
  secret_id = var.db_password_secret_arn
}

# Aurora Cluster
resource "aws_rds_cluster" "main" {
  cluster_identifier      = "${var.project_name}-${var.environment}-aurora-cluster"
  engine                  = "aurora-postgresql"
  engine_version          = "16.2"
  database_name           = var.db_name
  master_username         = var.db_username
  master_password         = data.aws_secretsmanager_secret_version.db_password.secret_string
  db_subnet_group_name    = aws_db_subnet_group.main.name
  vpc_security_group_ids  = [var.db_security_group_id]
  db_cluster_parameter_group_name = aws_rds_cluster_parameter_group.pgvector.name
  skip_final_snapshot     = true
  deletion_protection     = false
  backup_retention_period = 7
  preferred_backup_window = "03:00-04:00"
  preferred_maintenance_window = "mon:04:00-mon:05:00"
  enabled_cloudwatch_logs_exports = ["postgresql"]

  serverlessv2_scaling_configuration {
    max_capacity = var.aurora_max_capacity
    min_capacity = var.aurora_min_capacity
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-aurora-cluster"
  }
}

# Aurora Cluster Instance
resource "aws_rds_cluster_instance" "main" {
  count              = 1
  identifier         = "${var.project_name}-${var.environment}-aurora-instance-${count.index + 1}"
  cluster_identifier = aws_rds_cluster.main.id
  instance_class     = var.aurora_instance_class
  engine             = aws_rds_cluster.main.engine
  engine_version     = aws_rds_cluster.main.engine_version

  tags = {
    Name = "${var.project_name}-${var.environment}-aurora-instance-${count.index + 1}"
  }
}
