from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.deps import AuthContext, get_current_member
from app.schemas.documents import (
    CompleteUploadRequest,
    CompleteUploadResponse,
    DocumentListResponse,
    DocumentResponse,
    InitiateUploadRequest,
    InitiateUploadResponse,
)
from app.services.documents import (
    complete_document_upload,
    get_document,
    initiate_document_upload,
    list_documents,
)

router = APIRouter()


@router.get("/documents", response_model=DocumentListResponse)
async def get_documents(
    auth: AuthContext = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    return await list_documents(auth, db)


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document_detail(
    document_id: str,
    auth: AuthContext = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
) -> DocumentResponse:
    return await get_document(document_id, auth, db)


@router.post("/documents/upload-initiate", response_model=InitiateUploadResponse, status_code=201)
async def post_document_upload_initiate(
    payload: InitiateUploadRequest,
    auth: AuthContext = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
) -> InitiateUploadResponse:
    return await initiate_document_upload(payload, auth, db)


@router.post("/documents/{document_id}/complete-upload", response_model=CompleteUploadResponse)
async def post_document_complete_upload(
    document_id: str,
    payload: CompleteUploadRequest,
    auth: AuthContext = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
) -> CompleteUploadResponse:
    return await complete_document_upload(document_id, payload, auth, db)