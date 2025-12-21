# Terraform Infrastructure for Kavak Agent

This directory contains Terraform configuration to deploy the Kavak Agent application on AWS.

## Architecture

```
Usuario (HTTPS)
    ↓
API Gateway (REST API)
    ↓
VPC Link V2
    ↓
ALB Interno (privado)
    ↓
ECS Tasks en EC2 (privados)
    ↓
Aurora PostgreSQL + pgvector (privado)
```

## Prerequisites

1. AWS CLI configured with appropriate credentials
2. Terraform >= 1.5.0 installed
3. Access to create resources in AWS (VPC, ECS, RDS, API Gateway, etc.)

## Setup

1. Copy the example variables file:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

2. Edit `terraform.tfvars` with your specific values:
   - `db_username`: Database master username
   - Set other variables as needed

3. Set sensitive variables via environment variables or AWS Secrets Manager:
   ```bash
   export TF_VAR_db_username=your_username
   ```

4. Initialize Terraform:
   ```bash
   terraform init
   ```

5. Review the execution plan:
   ```bash
   terraform plan
   ```

6. Apply the configuration:
   ```bash
   terraform apply
   ```

## Secrets Management

The following secrets need to be populated in AWS Secrets Manager after initial deployment:

1. **OpenAI API Key**: `{project_name}-{environment}-openai-api-key`
   ```bash
   aws secretsmanager put-secret-value \
     --secret-id kavak-agent-production-openai-api-key \
     --secret-string "your-openai-api-key"
   ```

2. **Twilio Secrets**: `{project_name}-{environment}-twilio-secrets`

   The secret must be a JSON object with the following structure:
   ```json
   {
     "ACCOUNT_SID": "your-account-sid",
     "AUTH_TOKEN": "your-auth-token",
     "PHONE_NUMBER": "+1234567890"
   }
   ```

   To set it:
   ```bash
   aws secretsmanager put-secret-value \
     --secret-id kavak-agent-production-twilio-secrets \
     --secret-string '{"ACCOUNT_SID":"your-sid","AUTH_TOKEN":"your-token","PHONE_NUMBER":"+1234567890"}'
   ```

## Database URL

The database URL is automatically generated and stored in Secrets Manager after Aurora is created. The format is:
```
postgresql+asyncpg://{username}:{password}@{endpoint}:5432/{db_name}
```

## ECR Image Deployment

After the infrastructure is created, build and push your Docker image:

```bash
# Get login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(terraform output -raw ecr_repository_url | cut -d'/' -f1)

# Build image
docker build -t kavak-agent .

# Tag image
docker tag kavak-agent:latest $(terraform output -raw ecr_repository_url):latest

# Push image
docker push $(terraform output -raw ecr_repository_url):latest
```

## Outputs

After deployment, you can get important values:

```bash
# API Gateway URL
terraform output api_gateway_url

# Aurora endpoint
terraform output aurora_endpoint

# ECR repository URL
terraform output ecr_repository_url
```

## Module Structure

- `modules/vpc/` - VPC, subnets, NAT gateways, route tables
- `modules/security/` - Security groups, IAM roles, Secrets Manager
- `modules/aurora/` - Aurora PostgreSQL cluster with pgvector
- `modules/ecs/` - ECS cluster, task definition, service, auto scaling
- `modules/alb/` - Internal Application Load Balancer
- `modules/api-gateway/` - API Gateway REST API with VPC Link V2

## Important Notes

1. **pgvector Extension**: The Aurora parameter group is configured to enable the `vector` extension. After the cluster is created, you need to run:
   ```sql
   CREATE EXTENSION vector;
   ```

2. **Health Checks**: The application must have a `/health` endpoint that returns HTTP 200 for health checks to work.

3. **Auto Scaling**: ECS service auto-scales based on CPU (70%) and memory (80%) utilization.

4. **Costs**: This infrastructure includes NAT Gateways, Aurora Serverless v2, and EC2 instances which incur costs. Monitor your usage.

## Cleanup

To destroy all resources:

```bash
terraform destroy
```

**Warning**: This will delete all resources including the database. Make sure you have backups if needed.
