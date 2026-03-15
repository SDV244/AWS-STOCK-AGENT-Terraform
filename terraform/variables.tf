variable "aws_region" {
  default = "us-east-1"
}

variable "project_name" {
  default = "amzn-stock-agent"
}

variable "cognito_user_pool_name" {
  default = "stock-agent-user-pool"
}

variable "ecr_repo_name" {
  default = "amzn-stock-agent"
}