# Infrastructure — brfnapp on AWS ECS Fargate

Terraform definitions for the production stack hosting `https://brfnapp.com`.

## Topology

```
Internet ──▶ Route 53 ──▶ ACM (TLS 1.3) ──▶ WAF v2 ──▶ ALB (public subnets)
                                                          │
                                              ┌───────────┴───────────┐
                                              ▼                       ▼
                                         ECS Task 1              ECS Task 2
                                       (private subnet)        (private subnet)
                                              │                       │
                                              ├──▶ RDS MySQL 8.0 (private subnet)
                                              ├──▶ ElastiCache Redis 7 (private subnet)
                                              └──▶ SQS Queue
                                              
   VPC Endpoints (no NAT gateway):
     • S3 (gateway, free)        • Secrets Manager (interface)
     • ECR API + ECR DKR         • SQS (interface)
     • CloudWatch Logs (interface)
```

## Files

| File | Purpose |
|------|---------|
| `main.tf` | Terraform providers, S3+DynamoDB backend |
| `variables.tf` / `outputs.tf` | Inputs and exposed values |
| `vpc.tf` | VPC, subnets, IGW, route tables, VPC endpoints |
| `security_groups.tf` | ALB / ECS / RDS / Redis ingress rules |
| `alb.tf` | Application Load Balancer + target group + listeners |
| `waf.tf` | WAF v2 web ACL attached to the ALB |
| `ecs.tf` | ECS cluster, task definition, service (circuit-breaker rolling deploy) |
| `ecr.tf` | Container registry + lifecycle policy |
| `rds.tf` | MySQL 8.0 instance |
| `elasticache.tf` | Redis 7 cluster |
| `sqs.tf` | Main events queue + dead-letter queue |
| `secrets.tf` | DB credentials, Django secret, Stripe keys |
| `route53.tf` | Apex + www records aliasing the ALB |
| `acm.tf` | Wildcard TLS cert with DNS validation |
| `iam.tf` | ECS execution/task roles + GitHub Actions OIDC role |

## One-time bootstrap (local laptop)

```bash
# 1. State backend
aws s3api create-bucket --bucket brfnapp-terraform-state \
  --region eu-west-2 --create-bucket-configuration LocationConstraint=eu-west-2
aws s3api put-bucket-versioning --bucket brfnapp-terraform-state \
  --versioning-configuration Status=Enabled
aws s3api put-public-access-block --bucket brfnapp-terraform-state \
  --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
aws dynamodb create-table --table-name brfnapp-terraform-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST --region eu-west-2

# 2. Confirm Route 53 hosted zone for brfnapp.com exists in this AWS account
aws route53 list-hosted-zones-by-name --dns-name brfnapp.com

# 3. Apply
cp terraform.tfvars.example terraform.tfvars   # edit if needed
terraform init
terraform plan
terraform apply
```

After the first apply, copy the `github_actions_role_arn` output into the GitHub repo as the secret `AWS_ROLE_ARN`. From then on, all changes flow through the `Deploy` workflow on every push to `main`.

## Tear down

Run the `Destroy — Tear Down AWS Infrastructure` workflow from the GitHub Actions UI and type `destroy` in the confirmation field, or:

```bash
terraform destroy
```

`ALB + WAF cost money even when idle` — destroy when not actively demoing.
