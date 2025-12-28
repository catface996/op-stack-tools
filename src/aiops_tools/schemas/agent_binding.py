"""Agent-Tool binding schemas following constitution standards."""

from uuid import UUID

from pydantic import BaseModel, Field

from aiops_tools.schemas.tool import PaginationRequest, ToolResponse


# Request schemas
class BoundToolsRequest(PaginationRequest):
    """Request schema for querying bound tools (Constitution Principle V)."""

    agentId: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="External agent identifier",
    )
    keyword: str | None = Field(
        default=None,
        max_length=100,
        description="Search keyword for tool name or description",
    )
    categoryId: UUID | None = Field(
        default=None,
        description="Filter by category ID",
    )


class UnboundToolsRequest(PaginationRequest):
    """Request schema for querying unbound tools (Constitution Principle V)."""

    agentId: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="External agent identifier",
    )
    keyword: str | None = Field(
        default=None,
        max_length=100,
        description="Search keyword for tool name or description",
    )
    categoryId: UUID | None = Field(
        default=None,
        description="Filter by category ID",
    )


class BindToolsRequest(BaseModel):
    """Request schema for binding tools to an agent."""

    agentId: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="External agent identifier",
    )
    toolIds: list[UUID] = Field(
        default_factory=list,
        max_length=100,
        description="List of tool IDs to bind (empty to unbind all)",
    )


# Response schemas
class BindingPaginatedData(BaseModel):
    """Paginated data for binding queries (Constitution Principle V)."""

    content: list[ToolResponse]
    page: int
    size: int
    totalElements: int
    totalPages: int
    first: bool
    last: bool


class BindingListResponse(BaseModel):
    """Response for bound/unbound tools query (Constitution Principle V & VI)."""

    code: int = 0
    message: str = "success"
    success: bool = True
    data: BindingPaginatedData


class BindingResult(BaseModel):
    """Result data for bind tools operation."""

    agentId: str
    boundToolCount: int
    toolIds: list[UUID]


class BindToolsResponse(BaseModel):
    """Response for bind tools operation (Constitution Principle VI)."""

    code: int = 0
    message: str = "success"
    success: bool = True
    data: BindingResult
