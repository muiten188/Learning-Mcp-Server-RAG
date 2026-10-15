"""MCP server status HTTP route."""

from fastapi import APIRouter

from app.features.mcp.schemas import MCPServerStatus
from app.features.mcp.service import server_status

router = APIRouter(prefix="/api", tags=["mcp"])


@router.get(
    "/mcp-servers",
    response_model=list[MCPServerStatus],
    response_model_exclude_none=True,
)
async def mcp_servers() -> list[MCPServerStatus]:
    """Report whether the configured MCP tool server can be reached."""
    return await server_status()
