# S3 bucket for source PDFs (documents to ingest)
resource "aws_s3_bucket" "kb_docs" {
  bucket = "${var.project_name}-kb-docs-${data.aws_caller_identity.current.account_id}"
}

data "aws_caller_identity" "current" {}

resource "aws_s3_bucket_versioning" "kb_docs" {
  bucket = aws_s3_bucket.kb_docs.id
  versioning_configuration {
    status = "Enabled"
  }
}

output "kb_s3_bucket" {
  value = aws_s3_bucket.kb_docs.bucket
}

output "kb_s3_bucket_arn" {
  value = aws_s3_bucket.kb_docs.arn
}
