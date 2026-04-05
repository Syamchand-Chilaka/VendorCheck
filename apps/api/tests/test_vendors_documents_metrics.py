import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_vendor_create_list_and_detail(client: AsyncClient):
    create_resp = await client.post(
        "/api/v1/vendors",
        json={
            "name": "Greenfield Plumbing",
            "contact_email": "billing@greenfield.test",
            "metadata": {"category": "plumbing"},
        },
        headers={"X-Tenant-Id": "test-tenant-id"},
    )
    assert create_resp.status_code == 201
    vendor_id = create_resp.json()["id"]

    list_resp = await client.get(
        "/api/v1/vendors",
        headers={"X-Tenant-Id": "test-tenant-id"},
    )
    assert list_resp.status_code == 200
    assert len(list_resp.json()["items"]) == 1

    detail_resp = await client.get(
        f"/api/v1/vendors/{vendor_id}",
        headers={"X-Tenant-Id": "test-tenant-id"},
    )
    assert detail_resp.status_code == 200
    assert detail_resp.json()["name"] == "Greenfield Plumbing"


@pytest.mark.asyncio
async def test_document_upload_and_local_workflow_creates_review_task(client: AsyncClient):
    vendor_resp = await client.post(
        "/api/v1/vendors",
        json={"name": "Bank Vendor LLC"},
        headers={"X-Tenant-Id": "test-tenant-id"},
    )
    vendor_id = vendor_resp.json()["id"]

    initiate_resp = await client.post(
        "/api/v1/documents/upload-initiate",
        json={
            "vendor_id": vendor_id,
            "document_type": "bank_letter",
            "title": "Updated bank instructions",
            "original_filename": "bank-letter.pdf",
            "mime_type": "application/pdf",
            "file_size_bytes": 2048,
        },
        headers={"X-Tenant-Id": "test-tenant-id"},
    )
    assert initiate_resp.status_code == 201
    initiated = initiate_resp.json()
    assert initiated["upload_url"].startswith("https://example.invalid/")

    complete_resp = await client.post(
        f"/api/v1/documents/{initiated['document_id']}/complete-upload",
        json={"document_version_id": initiated["document_version_id"]},
        headers={"X-Tenant-Id": "test-tenant-id"},
    )
    assert complete_resp.status_code == 200
    completed = complete_resp.json()
    assert completed["workflow_status"] == "succeeded"

    review_resp = await client.get(
        "/api/v1/review-tasks",
        headers={"X-Tenant-Id": "test-tenant-id"},
    )
    assert review_resp.status_code == 200
    assert len(review_resp.json()["items"]) == 1


@pytest.mark.asyncio
async def test_metrics_summary_counts_objects(client: AsyncClient):
    vendor_resp = await client.post(
        "/api/v1/vendors",
        json={"name": "Metrics Vendor"},
        headers={"X-Tenant-Id": "test-tenant-id"},
    )
    vendor_id = vendor_resp.json()["id"]

    await client.post(
        "/api/v1/checks",
        data={"input_type": "paste_text", "raw_text": "Metrics Vendor\nhello"},
        headers={"X-Tenant-Id": "test-tenant-id"},
    )

    await client.post(
        "/api/v1/documents/upload-initiate",
        json={
            "vendor_id": vendor_id,
            "document_type": "other",
            "title": "W9",
            "original_filename": "w9.pdf",
            "mime_type": "application/pdf",
            "file_size_bytes": 1024,
        },
        headers={"X-Tenant-Id": "test-tenant-id"},
    )

    metrics_resp = await client.get(
        "/api/v1/metrics/summary",
        headers={"X-Tenant-Id": "test-tenant-id"},
    )
    assert metrics_resp.status_code == 200
    body = metrics_resp.json()
    assert body["total_vendors"] == 1
    assert body["total_documents"] == 1
    assert body["total_checks"] == 1
