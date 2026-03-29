"""Merge dual 006 branches (006_seed_seb_final + 006_add_conference_sessions).

Both branches descend from 005_insert_licenses. This merge migration resolves
the multiple-heads problem so alembic upgrade head can proceed linearly.

Revision ID: 006z_merge_006_branches
Revises: 006_seed_seb_final, 006_add_conference_sessions
Create Date: 2026-03-29
"""
from alembic import op
import sqlalchemy as sa

revision = "006z_merge_006_branches"
down_revision = ("006_seed_seb_final", "006_add_conference_sessions")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Merge only — no schema changes required.
    pass


def downgrade() -> None:
    pass
