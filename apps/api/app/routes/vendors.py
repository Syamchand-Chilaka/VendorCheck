from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.deps import AuthContext, get_current_member
from app.schemas.vendors import VendorCreateRequest, VendorListResponse, VendorResponse
from app.services.vendors import create_vendor, get_vendor, list_vendors

router = APIRouter()


@router.get("/vendors", response_model=VendorListResponse)
async def get_vendors(
    auth: AuthContext = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
) -> VendorListResponse:
    return await list_vendors(auth, db)


@router.post("/vendors", response_model=VendorResponse, status_code=201)
async def post_vendor(
    payload: VendorCreateRequest,
    auth: AuthContext = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
) -> VendorResponse:
    return await create_vendor(payload, auth, db)


@router.get("/vendors/{vendor_id}", response_model=VendorResponse)
async def get_vendor_detail(
    vendor_id: str,
    auth: AuthContext = Depends(get_current_member),
    db: AsyncSession = Depends(get_db),
) -> VendorResponse:
    return await get_vendor(vendor_id, auth, db)