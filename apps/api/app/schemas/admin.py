from uuid import UUID

from pydantic import BaseModel


class CreateRoleRequest(BaseModel):
    name: str
    description: str | None = None
    permissions: dict = {}


class RoleResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    permissions: dict

    model_config = {"from_attributes": True}


class DashboardStats(BaseModel):
    pending_research_articles: int
    pending_submissions: int
    total_knowledge_bases: int
    total_documents: int
    total_users: int
    low_rated_responses: int
    pending_user_approvals: int = 0
