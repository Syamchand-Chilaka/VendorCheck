from fastapi import APIRouter, Depends, Form, HTTPException
from supabase import Client

from app.deps import AuthContext, get_current_member, get_supabase
from app.schemas.checks import CreateCheckResponse
from app.services.checks import create_paste_text_check

router = APIRouter()


@router.post("/checks", response_model=CreateCheckResponse, status_code=201)
def post_check(
    input_type: str = Form(...),
    raw_text: str = Form(default=None),
    auth: AuthContext = Depends(get_current_member),
    supabase: Client = Depends(get_supabase),
) -> CreateCheckResponse:
    """Submit a new vendor verification check.

    Currently supports paste_text input only. PDF upload will be added
    in a later slice.
    """
    # Validate input_type
    if input_type not in ("paste_text", "pdf"):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid input_type: '{input_type}'. Must be 'paste_text' or 'pdf'.",
        )

    # PDF not implemented in this slice
    if input_type == "pdf":
        raise HTTPException(
            status_code=501,
            detail="PDF upload is not yet implemented. Use input_type=paste_text.",
        )

    # Validate raw_text for paste_text
    if not raw_text or not raw_text.strip():
        raise HTTPException(
            status_code=422,
            detail="raw_text is required and must not be empty when input_type is paste_text.",
        )

    return create_paste_text_check(raw_text.strip(), auth, supabase)
