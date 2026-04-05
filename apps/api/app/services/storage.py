from __future__ import annotations

import os
import re

import boto3

from app.config import get_settings


def _sanitize_filename(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-") or "document.pdf"


def build_document_s3_key(
    tenant_id: str,
    vendor_id: str,
    document_id: str,
    version_no: int,
    original_filename: str,
) -> str:
    safe_name = _sanitize_filename(original_filename)
    return (
        f"tenant/{tenant_id}/vendor/{vendor_id}/document/{document_id}/"
        f"version/{version_no}/{safe_name}"
    )


def generate_upload_url(bucket: str, s3_key: str, mime_type: str) -> str:
    settings = get_settings()
    if not bucket or settings.app_env in {"development", "test"}:
        return f"https://example.invalid/{bucket or 'local-bucket'}/{s3_key}"

    client = boto3.client("s3", region_name=settings.aws_region)
    return client.generate_presigned_url(
        "put_object",
        Params={"Bucket": bucket, "Key": s3_key, "ContentType": mime_type},
        ExpiresIn=900,
    )
