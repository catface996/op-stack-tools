"""Agent-Tool binding model."""

from uuid import UUID

from sqlalchemy import Index, String
from sqlmodel import Field, Relationship

from aiops_tools.models.base import BaseModel


class AgentToolBinding(BaseModel, table=True):
    """Agent-Tool binding relationship.

    Stores the many-to-many relationship between external agents
    (identified by string agentId) and tools in the system.
    """

    __tablename__ = "agent_tool_bindings"

    agent_id: str = Field(
        sa_type=String(255),
        index=True,
        nullable=False,
        description="External agent identifier (max 255 chars)",
    )
    tool_id: UUID = Field(
        foreign_key="tools.id",
        nullable=False,
        ondelete="CASCADE",
        description="Reference to bound tool",
    )

    # Relationships
    tool: "Tool" = Relationship()  # type: ignore[name-defined]

    __table_args__ = (
        Index(
            "idx_agent_tool_bindings_agent_tool",
            "agent_id",
            "tool_id",
            unique=True,
        ),
    )
