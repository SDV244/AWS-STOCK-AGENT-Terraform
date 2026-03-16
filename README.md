# AWS Agentcore Stock AI Agent

A production-grade AI agent deployed on AWS Agentcore Runtime that answers real-time and historical stock price queries for Amazon (AMZN), with document retrieval from Amazon's official financial reports.

---

## Architecture

```
User (Jupyter Notebook)
    │
    ▼ HTTPS POST + Cognito ID Token (Direct)
AWS Agentcore Runtime (Docker ARM64)
    │
    ├── Native Authorizer (Cognito JWT Discovery)
    │
    ▼
FastAPI + LangGraph ReAct Agent (.astream())
    │
    ├── retrieve_realtime_stock_price (yfinance)
    ├── retrieve_historical_stock_price (yfinance)
    └── retrieve_from_knowledge_base (Bedrock KB + S3 Vectors)
    │
    ├── Amazon Bedrock — Claude 3.5 Sonnet
    └── Langfuse — Observability
```

---

## Tech Stack

| Component | Technology |
|---|---|
| Agent Runtime | AWS Bedrock Agentcore |
| Agent Orchestration | LangGraph (ReAct) + `.astream()` |
| LLM | Claude 3.5 Sonnet (Bedrock Inference Profile) |
| Knowledge Base | Amazon Bedrock KB + S3 Vectors |
| Authentication | AWS Cognito User Pool (Native JWT Discovery) |
| Observability | Langfuse Cloud (free tier) |
| Stock Data | yfinance |
| Infrastructure | Terraform + PowerShell Automation |
| Language | Python 3.11 |
| Container | Docker ARM64 |

---

## Project Structure

```
amzn-stock-agent/
├── app/
│   ├── __init__.py
│   ├── agent.py          # LangGraph ReAct agent + astream()
│   ├── main.py           # FastAPI + AgentCore entrypoint
│   └── tools.py          # yfinance + Bedrock KB tools
├── terraform/
│   ├── main.tf           # Provider config
│   ├── variables.tf      # Input variables
│   ├── cognito.tf        # Cognito User Pool + App Client
│   ├── bedrock_kb.tf     # S3 bucket for source PDFs
│   ├── ecr.tf            # ECR repository
│   └── iam.tf            # IAM roles and policies
├── scripts/
│   └── setup_kb.py       # Creates S3 Vectors + Bedrock KB via boto3
├── notebook/
│   ├── demo.ipynb        # Demo notebook — just run all cells
│   └── screenshots/      # Langfuse trace screenshots
├── deploy_runtime.ps1    # Automated deployment script
├── artifact.json         # Runtime artifact configuration
├── jwt-auth.json         # Authorizer configuration (Cognito)
├── network.json          # Network configuration (Public)
├── .env.example          # Environment variables template
├── Dockerfile            # ARM64 container
├── requirements.txt      # Python dependencies
└── README.md
```

---

## Running the Demo Notebook (Evaluators)

No AWS credentials or infrastructure setup required. The endpoint is already deployed and live.

### Requirements

- Python 3.10+
- `pip install boto3 requests`

### Steps

1. Open `notebook/demo.ipynb`
2. Run **Kernel → Restart & Run All**

All queries will execute automatically against the direct Agentcore endpoint.

> **Note:** Cognito ID Tokens expire after 60 minutes. If you get `Signature has expired`, re-run the authentication cell (Cell 2).

---

## Full Deployment Guide (Infrastructure Owners)

### Prerequisites

- AWS Account with CLI configured (`aws configure`)
- Terraform >= 1.5.0
- Docker Desktop (configured for ARM64 builds)
- PowerShell 7+

---

### Step 1 — Clone and configure

```bash
git clone https://github.com/SDV244/AWS-STOCK-AGENT-Terraform.git
cd AWS-STOCK-AGENT-Terraform

cp .env.example .env
pip install -r requirements.txt
```

---

### Step 2 — Deploy infrastructure with Terraform

```bash
cd terraform
terraform init
terraform apply
```

---

### Step 3 — Setup Knowledge Base

Upload PDFs to the S3 bucket created by Terraform.

Run the KB setup script:

```bash
python scripts/setup_kb.py
```

---

### Step 4 — Build and Push Docker Image

```bash
# Build for ARM64
docker build --platform linux/arm64 -t amzn-stock-agent .

# Push to ECR (Follow AWS ECR console push commands)
```

---

### Step 5 — Configure Runtime Files

Ensure `artifact.json` has the correct `containerUri` and `jwt-auth.json` has your Cognito `discoveryUrl`.

---

### Step 6 — Automated Deployment

Instead of manual CLI commands, use the provided automation script:

```powershell
.\deploy_runtime.ps1
```

> **Note:** Ensure `env-config.json` is populated with your specific IDs before running.

---

## Queries Demonstrated

| Query | Tools Used |
|---|---|
| What is the stock price for Amazon right now? | retrieve_realtime_stock_price |
| What were the stock prices for Amazon in Q4 last year? | retrieve_historical_stock_price |
| Compare Amazon's recent performance to analyst predictions | Stock tools + KB |

---

## Environment Variables (Injected via env-config.json)

| Variable | Description |
|---|---|
| AWS_REGION | us-east-1 |
| COGNITO_USER_POOL_ID | From Terraform output |
| COGNITO_CLIENT_ID | From Terraform output |
| KNOWLEDGE_BASE_ID | From kb_outputs.json |
| BEDROCK_MODEL_ID | us.anthropic.claude-sonnet-4-20250514-v1:0 |
| LANGFUSE_PUBLIC_KEY | From Langfuse Dashboard |

---

## Cost Estimate

| Service | Estimated Monthly Cost |
|---|---|
| Agentcore Runtime | ~$0 (Serverless invocation) |
| S3 / Bedrock KB | ~$0.50 (Storage/Vectors) |
| Bedrock Claude 3.5 | ~$0.01 per 1K tokens |
| **Total** | **~$1–5/month (Pay-as-you-go)** |
