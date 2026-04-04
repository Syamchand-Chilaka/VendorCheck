"""Lambda handler for S3 document-upload events.

Starts a Step Functions execution for each uploaded document object using the
tenant/vendor/document identifiers encoded in the S3 key.
"""

import boto3
import json
import os
import re


def lambda_handler(event, context):
    """Handle S3 ObjectCreated events for uploaded documents."""
    state_machine_arn = os.environ.get("STATE_MACHINE_ARN", "")
    sfn = boto3.client("stepfunctions") if state_machine_arn else None

    results = []
    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        # Parse tenant/vendor/document/version from key
        # Expected format: tenant/{tenant_id}/vendor/{vendor_id}/document/{document_id}/version/{version_no}/raw.pdf
        match = re.match(
            r"tenant/(?P<tenant_id>[^/]+)/vendor/(?P<vendor_id>[^/]+)"
            r"/document/(?P<document_id>[^/]+)/version/(?P<version_no>[^/]+)/",
            key,
        )
        if not match:
            print(f"Skipping unrecognized key pattern: {key}")
            continue

        payload = {
            "tenant_id": match.group("tenant_id"),
            "vendor_id": match.group("vendor_id"),
            "document_id": match.group("document_id"),
            "document_version_id": record["s3"]["object"].get("versionId", ""),
            "version_no": match.group("version_no"),
            "bucket": bucket,
            "key": key,
            "correlation_id": context.aws_request_id if context else "local",
        }

        execution_arn = None
        if sfn is not None:
            response = sfn.start_execution(
                stateMachineArn=state_machine_arn,
                input=json.dumps(payload),
                name=f"doc-{match.group('document_id')}-{match.group('version_no')}-{payload['correlation_id'][:8]}",
            )
            execution_arn = response.get("executionArn")

        results.append({**payload, "execution_arn": execution_arn})
        print(f"Processed: {json.dumps(results[-1])}")

    return {"statusCode": 200, "processed": len(results)}
