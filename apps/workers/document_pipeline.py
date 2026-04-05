"""Worker entrypoints for document-processing events.

These handlers are intentionally thin. In non-production environments the API
falls back to local workflow execution, but these entrypoints provide the shape
needed for Lambda/Step Functions deployment.
"""

from __future__ import annotations


def handle_s3_event(event: dict) -> dict:
    records = event.get("Records", [])
    parsed = []
    for record in records:
        s3 = record.get("s3", {})
        bucket = s3.get("bucket", {}).get("name")
        key = s3.get("object", {}).get("key")
        parsed.append({"bucket": bucket, "key": key})
    return {"records": parsed}


def handle_step_functions_event(event: dict) -> dict:
    return {
        "tenant_id": event.get("tenant_id"),
        "document_id": event.get("document_id"),
        "document_version_id": event.get("document_version_id"),
        "status": "accepted",
    }
