"""Fix agents.user_id to match licenses.user_id (CLERK_ADMIN_USER_ID).

Root cause: Migration 007 seeded the agents row with a dev-mode hardcoded
Clerk ID ('user_3ASljZWeTNVAOMGP62n87Eq0GG9') instead of the real Clerk
admin user ID ('user_3ASrwDOrSTaDxCus6f1B5lnDsgz').

Migration 008 fixed licenses.user_id but only targeted the FC v3 UUID
('72dc5b7c-...'), not the dev-mode hardcoded ID in agents.

Result: agents.user_id != licenses.user_id → public profile endpoint returns
zero licenses (SELECT WHERE DBLicense.user_id == agent.user_id finds no rows).

Fix: update agents.user_id for 'seb' from old dev ID to the canonical Clerk ID.

Revision ID: 010_fix_agent_user_id
Revises: 009_dedup_licenses
Create Date: 2026-03-05
"""
from alembic import op

revision = "010_fix_agent_user_id"
down_revision = "009_dedup_licenses"
branch_labels = None
depends_on = None

OLD_AGENT_UID = "user_3ASljZWeTNVAOMGP62n87Eq0GG9"   # dev-mode hardcoded ID (wrong)
CORRECT_UID   = "user_3ASrwDOrSTaDxCus6f1B5lnDsgz"   # real Clerk admin user ID (matches licenses)


def upgrade() -> None:
    op.execute(
        f"UPDATE agents SET user_id = '{CORRECT_UID}' WHERE user_id = '{OLD_AGENT_UID}'"
    )


def downgrade() -> None:
    op.execute(
        f"UPDATE agents SET user_id = '{OLD_AGENT_UID}' WHERE user_id = '{CORRECT_UID}'"
    )
