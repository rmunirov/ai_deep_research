"""Initial schema: researches, events, cost tracking.

Revision ID: 001
Revises:
Create Date: 2026-04-06
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

research_status_enum = postgresql.ENUM(
    "pending",
    "planning",
    "searching",
    "analyzing",
    "writing",
    "reviewing",
    "completed",
    "failed",
    "cancelled",
    name="research_status",
    create_type=False,
)


def upgrade() -> None:
    research_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "researches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("query", sa.Text, nullable=False),
        sa.Column("status", research_status_enum, nullable=False, server_default="pending"),
        sa.Column("depth", sa.String(20), nullable=False, server_default="standard"),
        sa.Column("config_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("artifacts_dir", sa.Text, nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "research_events",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "research_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("researches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("agent_name", sa.String(50), nullable=True),
        sa.Column("payload", postgresql.JSONB, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_research_events_research_id", "research_events", ["research_id"])

    op.create_table(
        "cost_tracking",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "research_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("researches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("agent_name", sa.String(50), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("tokens_input", sa.Integer, nullable=False, server_default="0"),
        sa.Column("tokens_output", sa.Integer, nullable=False, server_default="0"),
        sa.Column(
            "estimated_cost_usd", sa.Numeric(10, 6), nullable=False, server_default="0"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_cost_tracking_research_id", "cost_tracking", ["research_id"])


def downgrade() -> None:
    op.drop_table("cost_tracking")
    op.drop_table("research_events")
    op.drop_table("researches")
    research_status_enum.drop(op.get_bind(), checkfirst=True)
