from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    model_config = ConfigDict(extra="ignore", env_file=".env")

    aws_region: str = "us-east-1"
    cognito_user_pool_id: str
    cognito_client_id: str
    knowledge_base_id: str
    kb_s3_bucket: str = ""
    langfuse_public_key: str
    langfuse_secret_key: str
    langfuse_host: str = "https://cloud.langfuse.com"
    bedrock_model_id: str = "anthropic.claude-3-5-sonnet-20241022-v2:0"

settings = Settings()