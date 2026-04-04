from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.deps import AuthContext, get_current_member
from app.schemas.checks import (
    CheckDecisionRequest,
    CheckDecisionResponse,
    CheckDetailResponse,
    CheckListResponse,
    CreateCheckResponse,
)
from app.services.checks import create_paste_text_check, decide_check, get_check_detail, list_checks

router = APIRouter()


@router.get("/checks", response_model=CheckListResponse)
async def get_checks(
    auth: AuthContext = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
) -> CheckListResponse:
    return await list_checks(auth, db)


@router.get("/checks/{check_id}", response_model=CheckDetailResponse)
async def get_check(
    check_id: str,
    auth: AuthContext = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
) -> CheckDetailResponse:
    return await get_check_detail(check_id, auth, db)


@router.post("/checks", response_model=CreateCheckResponse, status_code=201)
async def post_check(
    input_type: str = Form(...),
    raw_text: str = Form(default=None),
    auth: AuthContext = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
) -> CreateCheckResponse:
    """Submit a new vendor verification check.

    Currently supports paste_text input only. PDF upload will be added
    in a later slice.
    """
    if input_type not in ("paste_text", "pdf"):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid input_type: '{input_type}'. Must be 'paste_text' or 'pdf'.",
        )

    if input_type == "pdf":
        raise HTTPException(
            status_code=501,
            detail="PDF upload is not yet implemented. Use input_type=paste_text.",
        )

    if not raw_text or not raw_text.strip():
        raise HTTPException(
            status_code=422,
            detail="raw_text is required and must not be empty when input_type is paste_text.",
        )

    return await create_paste_text_check(raw_text.strip(), auth, db)


@router.post("/checks/{check_id}/decision", response_model=CheckDecisionResponse)
async def post_check_decision(
    check_id: str,
    payload: CheckDecisionRequest,
    auth: AuthContext = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
) -> CheckDecisionResponse:
    return await decide_check(check_id, payload, auth, db)
