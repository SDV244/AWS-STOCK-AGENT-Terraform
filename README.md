# AWS Agentcore Stock AI Agent

A production-grade AI agent deployed on AWS Agentcore Runtime that answers
real-time and historical stock price queries for Amazon (AMZN), with document
retrieval from Amazon's official financial reports.

## Architecture
```
User (Jupyter Notebook)
    │
    ▼ HTTPS POST + Cognito JWT
API Gateway (HTTP API)
    │ JWT validated automatically
    ▼
Lambda Function (proxy)
    │
    ▼
AWS Agentcore Runtime (Docker ARM64)
    │
    ▼
FastAPI + LangGraph ReAct Agent (.astream())
    │
    ├── retrieve_realtime_stock_price (yfinance)
    ├── retrieve_historical_stock_price (yfinance)
    └── retrieve_from_knowledge_base (Bedrock KB + S3 Vectors)
    │
    ├── Amazon Bedrock — Claude Sonnet 4
    └── Langfuse — Observability
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Agent Runtime | AWS Agentcore |
| API Layer | AWS API Gateway (HTTP API) + Lambda |
| Agent Orchestration | LangGraph (ReAct) + `.astream()` |
| LLM | Claude Sonnet 4 via Amazon Bedrock |
| Knowledge Base | Amazon Bedrock KB + S3 Vectors |
| Authentication | AWS Cognito User Pool (JWT) |
| Observability | Langfuse Cloud (free tier) |
| Stock Data | yfinance |
| Infrastructure | Terraform |
| Language | Python 3.11 |
| Container | Docker ARM64 |

## Project Structure
```
amzn-stock-agent/
├── app/
│   ├── __init__.py
│   ├── agent.py          # LangGraph ReAct agent + astream()
│   ├── auth.py           # Cognito JWT validation
│   ├── config.py         # Pydantic settings
│   ├── main.py           # FastAPI + AgentCore entrypoint
│   └── tools.py          # yfinance + Bedrock KB tools
├── terraform/
│   ├── main.tf           # Provider config
│   ├── variables.tf      # Input variables
│   ├── cognito.tf        # Cognito User Pool + App Client
│   ├── bedrock_kb.tf     # S3 bucket for source PDFs
│   ├── ecr.tf            # ECR repository
│   ├── iam.tf            # IAM roles and policies
│   ├── agentcore.tf      # Agentcore notes
│   └── apigateway.tf     # API Gateway + Lambda proxy
├── lambda/
│   └── handler.py        # Lambda proxy to Agentcore
├── scripts/
│   └── setup_kb.py       # Creates S3 Vectors + Bedrock KB via boto3
├── notebook/
│   ├── demo.ipynb        # Demo notebook — just run all cells
│   └── screenshots/      # Langfuse trace screenshots
├── .env.example          # Environment variables template
├── Dockerfile            # ARM64 container
├── requirements.txt      # Python dependencies
└── README.md
```

## Running the Demo Notebook (Evaluators)

**No AWS credentials or infrastructure setup required.**
The endpoint is already deployed and live.

### Requirements
<<<<<<< Updated upstream
- Python 3.10+
- `pip install boto3 requests`

### Steps
1. Open `notebook/demo.ipynb`
2. Run **Kernel → Restart & Run All**
3. All 5 queries will execute automatically

> **Note:** Cognito tokens expire after 60 minutes. If you get
> `Signature has expired`, re-run the authentication cell (Cell 2).

---

## Full Deployment Guide (Infrastructure Owners)

Follow these steps to deploy the full infrastructure from scratch.

### Prerequisites

- AWS Account with CLI configured (`aws configure`)
- Terraform >= 1.5.0 — https://developer.hashicorp.com/terraform/install
- Docker Desktop — https://www.docker.com/products/docker-desktop
- Python 3.10+
=======

- Python 3.10+
- `pip install boto3 requests`

### Steps

1. Open `notebook/demo.ipynb`
2. Run **Kernel → Restart & Run All**
3. All 5 queries will execute automatically

> **Note:** Cognito tokens expire after 60 minutes. If you get
> `Signature has expired`, re-run the authentication cell (Cell 2).

---

## Full Deployment Guide (Infrastructure Owners)

Follow these steps to deploy the full infrastructure from scratch.

### Prerequisites

- AWS Account with CLI configured (`aws configure`)
- Terraform >= 1.5.0 — <https://developer.hashicorp.com/terraform/install>
- Docker Desktop — <https://www.docker.com/products/docker-desktop>
- Python 3.10+
>>>>>>> Stashed changes

### Step 1 — Clone and configure
```bash
git clone https://github.com/SDV244/AWS-STOCK-AGENT-Terraform.git
cd AWS-STOCK-AGENT-Terraform

cp .env.example .env
pip install -r requirements.txt
```

### Step 2 — Deploy infrastructure with Terraform
```bash
cd terraform
terraform init
terraform apply
```

After apply completes run `terraform output` and copy values to `.env`:
<<<<<<< Updated upstream
=======

>>>>>>> Stashed changes
```
cognito_user_pool_id  → COGNITO_USER_POOL_ID
cognito_client_id     → COGNITO_CLIENT_ID
kb_s3_bucket          → KB_S3_BUCKET
kb_s3_bucket_arn      → KB_S3_BUCKET_ARN
bedrock_kb_role_arn   → BEDROCK_KB_ROLE_ARN
ecr_repository_url    → used in Step 6
api_gateway_url       → API_GATEWAY_URL
```

### Step 3 — Enable Bedrock Model Access

1. Go to **AWS Console → Amazon Bedrock → Model Access**
2. Enable:
   - `Amazon Titan Embeddings V2`
   - `Anthropic Claude Sonnet 4`
3. Wait until both show **Access granted**

### Step 4 — Setup Langfuse (free tier)

<<<<<<< Updated upstream
1. Sign up at https://cloud.langfuse.com
=======
1. Sign up at <https://cloud.langfuse.com>
>>>>>>> Stashed changes
2. Create project `amzn-stock-agent`
3. Go to **Settings → API Keys** → create a key pair
4. Add to `.env`:
```env
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

### Step 5 — Upload PDFs and create Knowledge Base
```powershell
# Download the 3 Amazon financial PDFs (PowerShell)
$urls = @(
  "https://s2.q4cdn.com/299287126/files/doc_financials/2025/ar/Amazon-2024-Annual-Report.pdf",
  "https://s2.q4cdn.com/299287126/files/doc_financials/2025/q3/AMZN-Q3-2025-Earnings-Release.pdf",
  "https://s2.q4cdn.com/299287126/files/doc_financials/2025/q2/AMZN-Q2-2025-Earnings-Release.pdf"
)
mkdir kb_docs
foreach ($url in $urls) {
  $file = Split-Path $url -Leaf
  Invoke-WebRequest -Uri $url -OutFile ".\kb_docs\$file"
}

# Upload to S3
aws s3 cp kb_docs\ s3://YOUR_KB_S3_BUCKET/ --recursive
```
```bash
# Create S3 Vectors bucket + Bedrock Knowledge Base
python scripts/setup_kb.py
```

Copy `KNOWLEDGE_BASE_ID` from `kb_outputs.json` into `.env`.

### Step 6 — Create Cognito test user
```bash
aws cognito-idp admin-create-user \
  --user-pool-id YOUR_COGNITO_USER_POOL_ID \
  --username testuser \
  --user-attributes Name=email,Value=testuser@example.com \
  --temporary-password TempPass1! \
  --region us-east-1

aws cognito-idp admin-set-user-password \
  --user-pool-id YOUR_COGNITO_USER_POOL_ID \
  --username testuser \
  --password PermanentPass1! \
  --permanent \
  --region us-east-1
```

### Step 7 — Request Agentcore quota increase

New AWS accounts have a default quota of 0 Agentcore runtimes.

1. Go to **AWS Console → Service Quotas → Amazon Bedrock**
2. Search `agent runtime` → **Maximum number of agent runtimes**
3. Request increase to `5`
4. Wait for approval email (24-48 hours)

### Step 8 — Install AgentCore CLI and configure
```bash
pip install bedrock-agentcore-starter-toolkit

agentcore configure \
  -e app/main.py \
  --execution-role arn:aws:iam::YOUR_ACCOUNT_ID:role/amzn-stock-agent-agentcore-role \
  --region us-east-1
```

When prompted:
- ECR repository → `amzn-stock-agent`
- Requirements file → `requirements.txt`
- OAuth → `no`
- Memory → `no`

### Step 9 — Deploy to Agentcore
```bash
agentcore deploy \
  --env AWS_REGION=us-east-1 \
  --env COGNITO_USER_POOL_ID=YOUR_VALUE \
  --env COGNITO_CLIENT_ID=YOUR_VALUE \
  --env KNOWLEDGE_BASE_ID=YOUR_VALUE \
  --env LANGFUSE_PUBLIC_KEY=YOUR_VALUE \
  --env LANGFUSE_SECRET_KEY=YOUR_VALUE \
  --env BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0
```

Wait until status is `READY`:
```bash
aws bedrock-agentcore-control list-agent-runtimes --region us-east-1
```

### Step 10 — Update notebook with your values

Update these variables in `notebook/demo.ipynb` Cell 1:
<<<<<<< Updated upstream
=======

>>>>>>> Stashed changes
```python
API_GATEWAY_URL      = "YOUR_API_GATEWAY_URL/prod"
COGNITO_USER_POOL_ID = "YOUR_VALUE"
COGNITO_CLIENT_ID    = "YOUR_VALUE"
```

Then run **Kernel → Restart & Run All**.

## Queries Demonstrated

| Query | Tools Used |
|-------|-----------|
| What is the stock price for Amazon right now? | `retrieve_realtime_stock_price` |
| What were the stock prices for Amazon in Q4 last year? | `retrieve_historical_stock_price` |
| Compare Amazon's recent stock performance to analyst predictions | Both stock tools + KB |
| Current price + AI business information | `retrieve_realtime_stock_price` + KB |
| Total office space in North America 2024 | `retrieve_from_knowledge_base` |

## Environment Variables

| Variable | Description | Source |
|----------|-------------|--------|
| `AWS_REGION` | AWS region | `us-east-1` |
| `COGNITO_USER_POOL_ID` | Cognito User Pool ID | Terraform output |
| `COGNITO_CLIENT_ID` | Cognito App Client ID | Terraform output |
| `KNOWLEDGE_BASE_ID` | Bedrock KB ID | `kb_outputs.json` |
| `KB_S3_BUCKET` | S3 bucket for PDFs | Terraform output |
| `KB_S3_BUCKET_ARN` | S3 bucket ARN | Terraform output |
| `BEDROCK_KB_ROLE_ARN` | IAM role for Bedrock KB | Terraform output |
| `BEDROCK_MODEL_ID` | Bedrock inference profile | `us.anthropic.claude-sonnet-4-20250514-v1:0` |
| `LANGFUSE_PUBLIC_KEY` | Langfuse public key | Langfuse dashboard |
| `LANGFUSE_SECRET_KEY` | Langfuse secret key | Langfuse dashboard |
| `LANGFUSE_HOST` | Langfuse host | `https://cloud.langfuse.com` |

## Known Issues and Solutions

| Issue | Solution |
|-------|----------|
| `SubscriptionRequiredException` on OpenSearch | Project uses S3 Vectors instead |
| `ServiceQuotaExceededException` on Agentcore | Request quota increase (Step 7) |
| `Signature has expired` in notebook | Re-run authentication cell |
| Model marked as Legacy | Use `us.anthropic.claude-sonnet-4-*` inference profile |
| Docker Hub rate limit in CodeBuild | Dockerfile uses `public.ecr.aws` mirror |
| Terraform does not support S3 Vectors as Bedrock KB backend | Use `scripts/setup_kb.py` instead |

## Cost Estimate

| Service | Estimated Monthly Cost |
|---------|----------------------|
| Agentcore Runtime | ~$0 (pay per invocation) |
| API Gateway | ~$0 (1M requests free) |
| Lambda | ~$0 (1M invocations free) |
| S3 Vectors | ~$0 (pay per query) |
| Bedrock Claude Sonnet 4 | ~$0.01 per 1K tokens |
| Cognito | Free (50K MAU free tier) |
| S3 Storage | ~$0.01 |
| ECR | ~$0.10 |
| **Total** | **~$1-5/month** |
