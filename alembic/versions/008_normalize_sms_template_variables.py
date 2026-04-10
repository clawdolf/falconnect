"""Normalize SMS template variables: {{name}} -> {first_name}, standardize syntax.

Revision ID: 018
Revises: 017
Create Date: 2026-04-09

Converts old double-brace template syntax to normalized single-brace format.
Also converts any remaining {{field}} patterns to {field}.
"""

import sqlalchemy as sa
from alembic import op

revision = "018_normalize_sms_variables"
down_revision = "017_add_activity_id_to_appointment_reminders"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Convert old template syntax to normalized format."""
    conn = op.get_bind()

    # Get all existing SMS templates
    result = conn.execute(sa.text("SELECT id, template_key, body FROM sms_templates"))
    rows = result.fetchall()

    if not rows:
        return

    for row in rows:
        template_id, key, body = row
        if not body:
            continue

        new_body = body
        # {{name}} -> {first_name}
        new_body = new_body.replace("{{name}}", "{first_name}")
        # Catch any remaining double-brace fields -> single brace
        new_body = new_body.replace("{{", "{").replace("}}", "}")

        if new_body != body:
            conn.execute(
                sa.text("UPDATE sms_templates SET body = :body WHERE id = :id"),
                {"body": new_body, "id": template_id},
            )


def downgrade() -> None:
    """Revert normalized syntax back to old double-brace format."""
    conn = op.get_bind()

    result = conn.execute(sa.text("SELECT id, template_key, body FROM sms_templates"))
    rows = result.fetchall()

    if not rows:
        return

    for row in rows:
        template_id, key, body = row
        if not body:
            continue

        new_body = body
        # {first_name} -> {{name}}
        new_body = new_body.replace("{first_name}", "{{name}}")
        # Other {field} -> {{field}} (but don't double-wrap already-wrapped)
        import re
        new_body = re.sub(r"\{([a-z_]+)\}", r"{{\1}}", new_body)

        if new_body != body:
            conn.execute(
                sa.text("UPDATE sms_templates SET body = :body WHERE id = :id"),
                {"body": new_body, "id": template_id},
            )
