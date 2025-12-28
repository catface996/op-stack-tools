"""API v1 router configuration."""

from fastapi import APIRouter

from aiops_tools.api.v1.endpoints import agent_binding, llm, tools

api_router = APIRouter()

api_router.include_router(tools.router)
api_router.include_router(llm.router, prefix="/llm", tags=["LLM"])
api_router.include_router(agent_binding.router, prefix="/agent-bindng", tags=["Agent Binding"])
