"""Add user_id to conference_sessions for ownership enforcement.

Existing rows are backfilled to the CLERK_ADMIN_USER_ID env var (Seb) so
single-operator history stays valid. New sessions will stamp the caller's
Clerk user_id at creation time.

Revision ID: 019_add_user_id_to_conference_sessions
Revises: 018_normalize_sms_variables
Create Date: 2026-04-17
"""
import os

import sqlalchemy as sa
from alembic import op

revision = "019_add_user_id_to_conference_sessions"
down_revision = "018_normalize_sms_variables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from sqlalchemy import inspect as sa_inspect

    bind = op.get_bind()
    cols = [c["name"] for c in sa_inspect(bind).get_columns("conference_sessions")]
    if "user_id" in cols:
        return

    # Add nullable, backfill, then enforce NOT NULL so Postgres doesn't reject
    # the migration on a non-empty table.
    op.add_column(
        "conference_sessions",
        sa.Column("user_id", sa.String(128), nullable=True),
    )

    seb = os.environ.get("CLERK_ADMIN_USER_ID", "user_3ASrwDOrSTaDxCus6f1B5lnDsgz")
    op.execute(
        sa.text("UPDATE conference_sessions SET user_id = :uid WHERE user_id IS NULL").bindparams(uid=seb)
    )

    op.alter_column("conference_sessions", "user_id", nullable=False)
    op.create_index(
        "ix_conference_sessions_user_id",
        "conference_sessions",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_conference_sessions_user_id", table_name="conference_sessions")
    op.drop_column("conference_sessions", "user_id")
