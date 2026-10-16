"""Add shared audit fields to existing entities."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision = "0002_audit_fields"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

TABLES = ("conversations", "messages", "tool_calls", "documents", "document_chunks")


def upgrade() -> None:
    """Add nullable actor IDs and backfill update times for existing rows."""
    for table in TABLES:
        op.add_column(table, sa.Column("created_by", UUID(as_uuid=True), nullable=True))
        op.add_column(table, sa.Column("updated_by", UUID(as_uuid=True), nullable=True))
        op.add_column(
            table,
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
        )
        if table != "document_chunks":
            op.execute(sa.text(f"UPDATE {table} SET updated_at = created_at"))
        op.alter_column(table, "updated_at", server_default=None)
        if table == "document_chunks":
            op.add_column(
                table,
                sa.Column(
                    "created_at",
                    sa.DateTime(timezone=True),
                    nullable=False,
                    server_default=sa.text("CURRENT_TIMESTAMP"),
                ),
            )
            op.alter_column(table, "created_at", server_default=None)


def downgrade() -> None:
    """Remove shared audit fields, retaining the original creation times."""
    for table in reversed(TABLES):
        if table == "document_chunks":
            op.drop_column(table, "created_at")
        op.drop_column(table, "updated_at")
        op.drop_column(table, "updated_by")
        op.drop_column(table, "created_by")
