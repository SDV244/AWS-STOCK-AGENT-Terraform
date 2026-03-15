# Amazon Stock AI Agent

A LangGraph ReAct agent deployed on AWS Agentcore Runtime with FastAPI,
streaming responses, Cognito auth, and Langfuse observability.

## Architecture

- **AWS Agentcore** — Managed agent runtime
- **Amazon Bedrock** — Claude 3.5 Sonnet (LLM) + Knowledge Base
- **AWS Cognito** — User authentication
- **LangGraph** — ReAct agent orchestration
- **Langfuse** — Observability and tracing
- **yfinance** — Real-time/historical stock data

## Prerequisites

- AWS CLI configured with appropriate permissions
- Terraform >= 1.5.0
- Docker Desktop
- Python 3.10+

## Deployment Steps

### 1. Clone and configure

git clone <repo_url>
cd amzn-stock-agent
cp .env.example .env

# Fill in your values in .env

### 2. Deploy infrastructure

cd terraform
terraform init
terraform apply

### 3. Upload knowledge base documents

aws s3 cp kb_docs/ s3://YOUR_BUCKET/ --recursive
aws bedrock-agent start-ingestion-job \
  --knowledge-base-id YOUR_KB_ID \
  --data-source-id YOUR_DS_ID

### 4. Build and push Docker image

aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin YOUR_ECR_URL

docker build -t amzn-stock-agent .
docker tag amzn-stock-agent:latest YOUR_ECR_URL:latest
docker push YOUR_ECR_URL:latest

### 5. Deploy to Agentcore

# See Phase 8.3 in the guide

### 6. Create Cognito test user

# See Phase 9 in the guide

### 7. Run the demo notebook

cd notebook
jupyter notebook demo.ipynb
