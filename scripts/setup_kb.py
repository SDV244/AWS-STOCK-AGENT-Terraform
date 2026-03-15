"""
Run this ONCE after terraform apply to:
  1. Create an S3 vector bucket
  2. Create a vector index inside it
  3. Create a Bedrock Knowledge Base backed by S3 Vectors
  4. Create the S3 data source (pointing to your PDF bucket)

Terraform does not yet support S3 Vectors as a Bedrock KB backend,
so this script handles that portion.

Usage:
    python scripts/setup_kb.py
"""

import boto3
import json
import time
from dotenv import load_dotenv
import os

load_dotenv()

REGION          = os.getenv("AWS_REGION", "us-east-1")
KB_ROLE_ARN     = os.getenv("BEDROCK_KB_ROLE_ARN")   # from terraform output
PDF_BUCKET_ARN  = os.getenv("KB_S3_BUCKET_ARN")       # from terraform output
PDF_BUCKET_NAME = os.getenv("KB_S3_BUCKET")           # from terraform output
PROJECT         = os.getenv("PROJECT_NAME", "amzn-stock-agent")

VECTOR_BUCKET_NAME = f"{PROJECT}-vectors"
VECTOR_INDEX_NAME  = f"{PROJECT}-index"
KB_NAME            = f"{PROJECT}-kb"

# ── Clients ──────────────────────────────────────────────────────────────────
s3vectors     = boto3.client("s3vectors",    region_name=REGION)
bedrock_agent = boto3.client("bedrock-agent", region_name=REGION)


def create_vector_bucket():
    print(f"Creating S3 vector bucket: {VECTOR_BUCKET_NAME}")
    try:
        s3vectors.create_vector_bucket(vectorBucketName=VECTOR_BUCKET_NAME)
        print("  ✅ Vector bucket created")
    except s3vectors.exceptions.ConflictException:
        print("  ⚠️  Vector bucket already exists — skipping")


def create_vector_index():
    print(f"Creating vector index: {VECTOR_INDEX_NAME}")
    try:
        s3vectors.create_index(
            vectorBucketName=VECTOR_BUCKET_NAME,
            indexName=VECTOR_INDEX_NAME,
            dataType="float32",
            dimension=1024,          # Titan Embed Text V2 output dimension
            distanceMetric="cosine",
        )
        print("  ✅ Vector index created")
    except s3vectors.exceptions.ConflictException:
        print("  ⚠️  Vector index already exists — skipping")


def get_vector_bucket_arn() -> str:
    resp = s3vectors.get_vector_bucket(vectorBucketName=VECTOR_BUCKET_NAME)
    return resp["vectorBucket"]["vectorBucketArn"]


def get_vector_index_arn() -> str:
    resp = s3vectors.get_index(
        vectorBucketName=VECTOR_BUCKET_NAME,
        indexName=VECTOR_INDEX_NAME,
    )
    return resp["index"]["indexArn"]


def create_knowledge_base(vector_bucket_arn: str, vector_index_arn: str) -> str:
    print(f"Creating Bedrock Knowledge Base: {KB_NAME}")
    try:
        resp = bedrock_agent.create_knowledge_base(
            name=KB_NAME,
            description="Amazon financial documents: 2024 Annual Report, Q2/Q3 2025 Earnings",
            roleArn=KB_ROLE_ARN,
            knowledgeBaseConfiguration={
                "type": "VECTOR",
                "vectorKnowledgeBaseConfiguration": {
                    "embeddingModelArn": (
                        f"arn:aws:bedrock:{REGION}::foundation-model/"
                        "amazon.titan-embed-text-v2:0"
                    ),
                    "embeddingModelConfiguration": {
                        "bedrockEmbeddingModelConfiguration": {
                            "dimensions": 1024,
                            "embeddingDataType": "FLOAT32",
                        }
                    },
                },
            },
            storageConfiguration={
                "type": "S3_VECTORS",
                "s3VectorsConfiguration": {
                    "vectorBucketArn": vector_bucket_arn,
                    "indexArn": vector_index_arn,
                },
            },
        )
        kb_id = resp["knowledgeBase"]["knowledgeBaseId"]
        print(f"  ✅ Knowledge Base created: {kb_id}")
        return kb_id
    except bedrock_agent.exceptions.ConflictException:
        kbs   = bedrock_agent.list_knowledge_bases()["knowledgeBaseSummaries"]
        kb_id = next(kb["knowledgeBaseId"] for kb in kbs if kb["name"] == KB_NAME)
        print(f"  ⚠️  KB already exists: {kb_id}")
        return kb_id


def wait_for_kb(kb_id: str):
    print("  ⏳ Waiting for KB to become ACTIVE...")
    for _ in range(30):
        resp   = bedrock_agent.get_knowledge_base(knowledgeBaseId=kb_id)
        status = resp["knowledgeBase"]["status"]
        if status == "ACTIVE":
            print("  ✅ KB is ACTIVE")
            return
        print(f"     status: {status} — retrying in 10s")
        time.sleep(10)
    raise TimeoutError("KB did not become ACTIVE in time")


def create_data_source(kb_id: str) -> str:
    print(f"Creating S3 data source pointing to: {PDF_BUCKET_NAME}")
    try:
        resp = bedrock_agent.create_data_source(
            knowledgeBaseId=kb_id,
            name="amazon-financial-pdfs",
            dataSourceConfiguration={
                "type": "S3",
                "s3Configuration": {
                    "bucketArn": PDF_BUCKET_ARN,
                },
            },
            vectorIngestionConfiguration={
                "chunkingConfiguration": {
                    "chunkingStrategy": "FIXED_SIZE",
                    "fixedSizeChunkingConfiguration": {
                        "maxTokens":         512,
                        "overlapPercentage": 20,
                    },
                }
            },
        )
        ds_id = resp["dataSource"]["dataSourceId"]
        print(f"  ✅ Data source created: {ds_id}")
        return ds_id
    except Exception as e:
        print(f"  ⚠️  Data source may already exist: {e}")
        sources = bedrock_agent.list_data_sources(knowledgeBaseId=kb_id)["dataSourceSummaries"]
        return sources[0]["dataSourceId"]


def start_ingestion(kb_id: str, ds_id: str):
    print("Starting ingestion job...")
    resp   = bedrock_agent.start_ingestion_job(
        knowledgeBaseId=kb_id,
        dataSourceId=ds_id,
    )
    job_id = resp["ingestionJob"]["ingestionJobId"]
    print(f"  ✅ Ingestion started: {job_id}")

    print("  ⏳ Waiting for ingestion to complete (this may take a few minutes)...")
    for _ in range(60):
        job    = bedrock_agent.get_ingestion_job(
            knowledgeBaseId=kb_id,
            dataSourceId=ds_id,
            ingestionJobId=job_id,
        )["ingestionJob"]
        status = job["status"]
        if status == "COMPLETE":
            stats = job.get("statistics", {})
            print(f"  ✅ Ingestion COMPLETE — {stats}")
            return
        if status == "FAILED":
            raise RuntimeError(f"Ingestion FAILED: {job.get('failureReasons')}")
        print(f"     status: {status} — retrying in 15s")
        time.sleep(15)
    raise TimeoutError("Ingestion did not complete in time")


def save_outputs(kb_id: str, ds_id: str):
    """Write KB ID to a local file so other scripts/env can pick it up."""
    outputs = {"KNOWLEDGE_BASE_ID": kb_id, "DATA_SOURCE_ID": ds_id}
    with open("kb_outputs.json", "w") as f:
        json.dump(outputs, f, indent=2)
    print(f"\n📄 Saved to kb_outputs.json")
    print(f"   → Add to your .env:  KNOWLEDGE_BASE_ID={kb_id}")


if __name__ == "__main__":
    create_vector_bucket()
    create_vector_index()

    vb_arn  = get_vector_bucket_arn()
    vi_arn  = get_vector_index_arn()
    print(f"  Vector bucket ARN: {vb_arn}")
    print(f"  Vector index ARN:  {vi_arn}")

    kb_id = create_knowledge_base(vb_arn, vi_arn)
    wait_for_kb(kb_id)

    ds_id = create_data_source(kb_id)
    start_ingestion(kb_id, ds_id)

    save_outputs(kb_id, ds_id)
    print("\n🎉 S3 Vectors Knowledge Base fully set up!")