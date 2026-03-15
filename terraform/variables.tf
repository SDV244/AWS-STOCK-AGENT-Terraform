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
variable "agent_runtime_arn" {
  default = "arn:aws:bedrock-agentcore:us-east-1:551670267045:runtime/app_main-X3Fu7U6ukU"
}
