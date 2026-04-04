"""Placeholder Lambda handler for document upload events.

This will be replaced with the real implementation in Phase 6.
"""

import json
import os
import re


def lambda_handler(event, context):
    """Handle S3 ObjectCreated events for uploaded documents."""
    state_machine_arn = os.environ.get("STATE_MACHINE_ARN", "")

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
            "document_version_id": match.group("version_no"),
            "bucket": bucket,
            "key": key,
            "correlation_id": context.aws_request_id if context else "local",
        }

        results.append(payload)
        print(f"Processed: {json.dumps(payload)}")

        # TODO Phase 6: Start Step Functions execution
        # sfn = boto3.client("stepfunctions")
        # sfn.start_execution(
        #     stateMachineArn=state_machine_arn,
        #     input=json.dumps(payload),
        # )

    return {"statusCode": 200, "processed": len(results)}
