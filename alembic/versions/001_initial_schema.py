"""Initial schema — lead_xref, sync_log, issued_paid, analytics_daily.

Revision ID: 001_initial
Revises:
Create Date: 2026-03-03
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lead_xref",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ghl_contact_id", sa.String(length=64), nullable=False),
        sa.Column("notion_page_id", sa.String(length=64), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("first_name", sa.String(length=128), nullable=True),
        sa.Column("last_name", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ghl_contact_id"),
        sa.UniqueConstraint("notion_page_id"),
    )
    op.create_index("ix_lead_xref_ghl_contact_id", "lead_xref", ["ghl_contact_id"])
    op.create_index("ix_lead_xref_notion_page_id", "lead_xref", ["notion_page_id"])
    op.create_index("ix_lead_xref_phone", "lead_xref", ["phone"])

    op.create_table(
        "sync_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("direction", sa.String(length=16), nullable=False),
        sa.Column("source_id", sa.String(length=128), nullable=True),
        sa.Column("target_id", sa.String(length=128), nullable=True),
        sa.Column("payload", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="ok"),
        sa.Column("error_detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sync_log_event_type", "sync_log", ["event_type"])

    op.create_table(
        "issued_paid",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("carrier", sa.String(length=128), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("transaction_date", sa.Date(), nullable=False),
        sa.Column("plaid_transaction_id", sa.String(length=128), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("plaid_transaction_id"),
    )

    op.create_table(
        "analytics_daily",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("dials", sa.Integer(), server_default="0"),
        sa.Column("contacts", sa.Integer(), server_default="0"),
        sa.Column("appointments_set", sa.Integer(), server_default="0"),
        sa.Column("appointments_kept", sa.Integer(), server_default="0"),
        sa.Column("closes", sa.Integer(), server_default="0"),
        sa.Column("premium_submitted", sa.Float(), server_default="0.0"),
        sa.Column("premium_issued", sa.Float(), server_default="0.0"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("date"),
    )
    op.create_index("ix_analytics_daily_date", "analytics_daily", ["date"])


def downgrade() -> None:
    op.drop_table("analytics_daily")
    op.drop_table("issued_paid")
    op.drop_table("sync_log")
    op.drop_table("lead_xref")
