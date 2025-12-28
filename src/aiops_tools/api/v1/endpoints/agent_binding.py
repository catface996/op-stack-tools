"""Agent-Tool binding API endpoints - All POST mode (Constitution Principle II)."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from aiops_tools.core.database import get_session

from aiops_tools.core.errors import ValidationError
from aiops_tools.models import Tool, ToolStatus
from aiops_tools.models.agent_binding import AgentToolBinding
from aiops_tools.schemas.agent_binding import (
    BindingListResponse,
    BindingPaginatedData,
    BindingResult,
    BindToolsRequest,
    BindToolsResponse,
    BoundToolsRequest,
    UnboundToolsRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter()

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post("/bound", response_model=BindingListResponse, tags=["Agent Binding"])
async def query_bound_tools(
    session: SessionDep, request: BoundToolsRequest
) -> BindingListResponse:
    """Query all tools bound to a specific agent (Constitution Principle V & VI compliant)."""
    logger.info(
        "Querying bound tools for agent: %s (keyword=%s, categoryId=%s)",
        request.agentId,
        request.keyword,
        request.categoryId,
    )
    # Build query for bound tools
    query = (
        select(Tool)
        .join(AgentToolBinding, Tool.id == AgentToolBinding.tool_id)
        .where(AgentToolBinding.agent_id == request.agentId)
        .where(Tool.status == ToolStatus.ACTIVE)
        .options(selectinload(Tool.category))
    )

    # Apply keyword filter (search in name and description)
    if request.keyword:
        keyword_pattern = f"%{request.keyword}%"
        query = query.where(
            or_(
                Tool.name.ilike(keyword_pattern),
                Tool.description.ilike(keyword_pattern),
            )
        )

    # Apply category filter
    if request.categoryId:
        query = query.where(Tool.category_id == request.categoryId)

    query = query.order_by(Tool.name)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_elements = await session.scalar(count_query) or 0

    # Apply pagination
    query = query.offset((request.page - 1) * request.size).limit(request.size)
    result = await session.execute(query)
    tools = list(result.scalars().all())

    # Calculate pagination metadata
    total_pages = (total_elements + request.size - 1) // request.size if request.size > 0 else 0
    is_first = request.page == 1
    is_last = request.page >= total_pages if total_pages > 0 else True

    logger.info(
        "Found %d bound tools for agent %s (page %d/%d)",
        total_elements,
        request.agentId,
        request.page,
        total_pages,
    )
    return BindingListResponse(
        code=0,
        message="success",
        success=True,
        data=BindingPaginatedData(
            content=tools,
            page=request.page,
            size=request.size,
            totalElements=total_elements,
            totalPages=total_pages,
            first=is_first,
            last=is_last,
        ),
    )


@router.post("/unbound", response_model=BindingListResponse, tags=["Agent Binding"])
async def query_unbound_tools(
    session: SessionDep, request: UnboundToolsRequest
) -> BindingListResponse:
    """Query all active tools NOT bound to a specific agent (Constitution Principle V & VI compliant)."""
    logger.info(
        "Querying unbound tools for agent: %s (keyword=%s, categoryId=%s)",
        request.agentId,
        request.keyword,
        request.categoryId,
    )
    # Subquery to get tool IDs bound to this agent
    bound_tool_ids_subquery = select(AgentToolBinding.tool_id).where(
        AgentToolBinding.agent_id == request.agentId
    )

    # Build query for unbound tools
    query = (
        select(Tool)
        .where(Tool.status == ToolStatus.ACTIVE)
        .where(Tool.id.notin_(bound_tool_ids_subquery))
        .options(selectinload(Tool.category))
    )

    # Apply keyword filter (search in name and description)
    if request.keyword:
        keyword_pattern = f"%{request.keyword}%"
        query = query.where(
            or_(
                Tool.name.ilike(keyword_pattern),
                Tool.description.ilike(keyword_pattern),
            )
        )

    # Apply category filter
    if request.categoryId:
        query = query.where(Tool.category_id == request.categoryId)

    query = query.order_by(Tool.name)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_elements = await session.scalar(count_query) or 0

    # Apply pagination
    query = query.offset((request.page - 1) * request.size).limit(request.size)
    result = await session.execute(query)
    tools = list(result.scalars().all())

    # Calculate pagination metadata
    total_pages = (total_elements + request.size - 1) // request.size if request.size > 0 else 0
    is_first = request.page == 1
    is_last = request.page >= total_pages if total_pages > 0 else True

    logger.info(
        "Found %d unbound tools for agent %s (page %d/%d)",
        total_elements,
        request.agentId,
        request.page,
        total_pages,
    )
    return BindingListResponse(
        code=0,
        message="success",
        success=True,
        data=BindingPaginatedData(
            content=tools,
            page=request.page,
            size=request.size,
            totalElements=total_elements,
            totalPages=total_pages,
            first=is_first,
            last=is_last,
        ),
    )


@router.post("/bindng", response_model=BindToolsResponse, tags=["Agent Binding"])
async def bind_tools(session: SessionDep, request: BindToolsRequest) -> BindToolsResponse:
    """Bind tools to an agent using full replacement semantics (Constitution Principle VI compliant).

    This operation replaces ALL existing bindings for the agent with the provided tool IDs.
    Pass an empty toolIds array to unbind all tools from the agent.
    """
    logger.info(
        "Binding %d tools to agent %s (full replacement)",
        len(request.toolIds),
        request.agentId,
    )
    # Deduplicate tool IDs (FR-008)
    unique_tool_ids = list(set(request.toolIds))

    # Validate all tool IDs exist and are active (FR-005)
    if unique_tool_ids:
        valid_tools_query = select(Tool.id).where(
            Tool.id.in_(unique_tool_ids),
            Tool.status == ToolStatus.ACTIVE,
        )
        result = await session.execute(valid_tools_query)
        valid_tool_ids = set(result.scalars().all())

        # Find invalid tool IDs
        invalid_tool_ids = set(unique_tool_ids) - valid_tool_ids
        if invalid_tool_ids:
            logger.warning(
                "Invalid tool IDs for agent %s: %s",
                request.agentId,
                [str(tid) for tid in invalid_tool_ids],
            )
            raise ValidationError(
                message="Some tool IDs do not exist or are not active",
                field="toolIds",
                suggestion="Use POST /api/tools/v1/tools/list to see available active tools",
                details={"invalidIds": [str(tid) for tid in invalid_tool_ids]},
            )

    # Full replacement: Delete existing bindings for this agent
    await session.execute(
        delete(AgentToolBinding).where(AgentToolBinding.agent_id == request.agentId)
    )

    # Insert new bindings
    bound_tool_ids = []
    for tool_id in unique_tool_ids:
        binding = AgentToolBinding(agent_id=request.agentId, tool_id=tool_id)
        session.add(binding)
        bound_tool_ids.append(tool_id)

    await session.flush()

    logger.info(
        "Successfully bound %d tools to agent %s",
        len(bound_tool_ids),
        request.agentId,
    )
    return BindToolsResponse(
        code=0,
        message="success",
        success=True,
        data=BindingResult(
            agentId=request.agentId,
            boundToolCount=len(bound_tool_ids),
            toolIds=bound_tool_ids,
        ),
    )
