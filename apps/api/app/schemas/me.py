from pydantic import BaseModel


class UserInfo(BaseModel):
    id: str
    email: str
    display_name: str
    email_verified: bool


class MembershipInfo(BaseModel):
    tenant_id: str
    tenant_name: str
    role: str


class MeResponse(BaseModel):
    user: UserInfo
    memberships: list[MembershipInfo]
