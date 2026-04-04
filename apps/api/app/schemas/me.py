from pydantic import BaseModel


class UserInfo(BaseModel):
    id: str
    email: str
    display_name: str
    email_verified: bool


class WorkspaceInfo(BaseModel):
    id: str
    name: str
    role: str


class MeResponse(BaseModel):
    user: UserInfo
    workspace: WorkspaceInfo
