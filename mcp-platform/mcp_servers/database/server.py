"""Read-only database MCP server deployed separately from FastAPI."""

import os

from mcp.server.mcpserver import MCPServer
from sqlalchemy import Column, MetaData, Table, Uuid, func, select
from sqlalchemy.ext.asyncio import create_async_engine

mcp = MCPServer("database")
metadata = MetaData()
TABLES = {
    name: Table(name, metadata, Column("id", Uuid(as_uuid=True), primary_key=True))
    for name in (
        "conversations",
        "messages",
        "tool_calls",
        "documents",
        "document_chunks",
    )
}


@mcp.tool()
async def database_summary() -> str:
    """Report read-only row counts for application tables.

    Returns:
        Table names and their row counts.

    Raises:
        RuntimeError: If DATABASE_URL is not configured.
    """
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is required")
    engine = create_async_engine(url, pool_pre_ping=True)
    try:
        async with engine.connect() as connection:
            counts = {
                name: await connection.scalar(select(func.count()).select_from(table))
                for name, table in TABLES.items()
            }
        return "; ".join(f"{name}: {count}" for name, count in counts.items())
    finally:
        await engine.dispose()


@mcp.tool()
async def database_tables() -> str:
    """List application tables exposed for read-only reports.

    Returns:
        Registered table names.
    """
    return ", ".join(sorted(TABLES))


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=int(
            os.environ.get("MCP_DATABASE_PORT", os.environ.get("MCP_PORT", "8103"))
        ),
        stateless_http=True,
    )
