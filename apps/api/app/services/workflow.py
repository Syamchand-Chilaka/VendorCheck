from __future__ import annotations

from datetime import datetime

import boto3
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.orm import (
    Alert,
    Document,
    DocumentArtifact,
    DocumentVersion,
    ExtractedField,
    ReviewTask,
    RiskSignal,
    ValidationResult,
    Vendor,
    WorkflowRun,
)
from app.services.audit import log_audit_event, record_metric_event


async def _run_local_document_pipeline(
    db: AsyncSession,
    *,
    tenant_id: str,
    document: Document,
    version: DocumentVersion,
    vendor: Vendor,
    workflow_run: WorkflowRun,
) -> None:
    hint = f"{document.document_type or ''} {document.title or ''} {version.original_filename or ''}".lower()
    needs_review = document.document_type == "bank_letter" or "bank" in hint
    confidence = 0.72 if needs_review else 0.94
    verdict = "verify" if needs_review else "safe"
    risk_score = 68 if needs_review else 12
    explanation = (
        "Document indicates bank-detail-related change and requires manual verification."
        if needs_review
        else "Document passed stub validation without high-risk indicators."
    )
    recommended_action = (
        "Route to reviewer before accepting vendor change."
        if needs_review
        else "Accept and retain for audit history."
    )

    db.add(
        DocumentArtifact(
            document_version_id=version.id,
            tenant_id=tenant_id,
            artifact_type="extracted_text",
            content_text=f"{vendor.name} {document.title or ''} {version.original_filename or ''}".strip(),
        )
    )
    db.add(
        ExtractedField(
            document_version_id=version.id,
            tenant_id=tenant_id,
            field_name="vendor_name",
            field_value=vendor.name,
            confidence=0.99,
        )
    )
    db.add(
        ValidationResult(
            document_version_id=version.id,
            tenant_id=tenant_id,
            validator_type="stub",
            verdict=verdict,
            risk_score=risk_score,
            confidence=confidence,
            explanation=explanation,
            recommended_action=recommended_action,
            raw_response="{\"mode\": \"local_stub\"}",
        )
    )

    if needs_review:
        signal = RiskSignal(
            tenant_id=tenant_id,
            document_version_id=version.id,
            signal_type="bank_change_detected",
            severity="high",
            title="Bank detail document requires review",
            description="Local workflow flagged a bank-related document for human review.",
        )
        task = ReviewTask(
            tenant_id=tenant_id,
            document_id=document.id,
            document_version_id=version.id,
            status="open",
            priority=80,
        )
        db.add(signal)
        db.add(task)
        await db.flush()
        db.add(
            Alert(
                tenant_id=tenant_id,
                alert_type="review_needed",
                document_id=document.id,
                review_task_id=task.id,
                message=f"Document '{document.title or version.original_filename}' needs review.",
            )
        )
        document.status = "review_needed"
        version.status = "review_needed"
        await record_metric_event(
            db,
            tenant_id=tenant_id,
            event_type="document_review_needed",
            entity_type="document",
            entity_id=document.id,
            value=risk_score,
        )
    else:
        document.status = "validated"
        version.status = "validated"
        await record_metric_event(
            db,
            tenant_id=tenant_id,
            event_type="document_validated",
            entity_type="document",
            entity_id=document.id,
            value=risk_score,
        )

    workflow_run.status = "succeeded"
    workflow_run.completed_at = datetime.utcnow()
    await log_audit_event(
        db,
        tenant_id=tenant_id,
        user_id=document.created_by,
        action="workflow.completed",
        entity_type="document_version",
        entity_id=version.id,
        details={"workflow_run_id": workflow_run.id, "mode": "local_stub"},
    )


async def start_document_workflow(
    db: AsyncSession,
    *,
    tenant_id: str,
    document: Document,
    version: DocumentVersion,
    vendor: Vendor,
) -> WorkflowRun:
    settings = get_settings()
    workflow_run = WorkflowRun(
        tenant_id=tenant_id,
        document_version_id=version.id,
        status="running",
    )
    db.add(workflow_run)
    await db.flush()

    await log_audit_event(
        db,
        tenant_id=tenant_id,
        user_id=document.created_by,
        action="workflow.started",
        entity_type="document_version",
        entity_id=version.id,
        details={"workflow_run_id": workflow_run.id},
    )
    await record_metric_event(
        db,
        tenant_id=tenant_id,
        event_type="workflow_started",
        entity_type="document_version",
        entity_id=version.id,
    )

    if settings.step_functions_state_machine_arn and settings.app_env not in {"development", "test"}:
        client = boto3.client("stepfunctions", region_name=settings.aws_region)
        response = client.start_execution(
            stateMachineArn=settings.step_functions_state_machine_arn,
            input=(
                "{"
                f'\"tenant_id\": \"{tenant_id}\", '
                f'\"document_id\": \"{document.id}\", '
                f'\"document_version_id\": \"{version.id}\"'
                "}"
            ),
        )
        workflow_run.sfn_execution_arn = response.get("executionArn")
        version.status = "queued"
        document.status = "queued"
        return workflow_run

    await _run_local_document_pipeline(
        db,
        tenant_id=tenant_id,
        document=document,
        version=version,
        vendor=vendor,
        workflow_run=workflow_run,
    )
    return workflow_run