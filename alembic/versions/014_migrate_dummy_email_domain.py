"""Migrate dummy email domain from cal.falconnect.org to appt.invalid.

Close CRM's contact enrichment resolves cal.falconnect.org to Falcon Financial,
pulling the company logo onto every lead contact record. RFC 2606 reserves .invalid
as a TLD that will never resolve — no logo, no brand association.

Revision ID: 014_migrate_dummy_email_domain
Revises: 013_add_sms_templates_phone_numbers
Create Date: 2026-03-19
"""
from alembic import op

revision = "014_migrate_dummy_email_domain"
down_revision = "013_add_sms_templates_phone_numbers"
branch_labels = None
depends_on = None

OLD_DOMAIN = "@cal.falconnect.org"
NEW_DOMAIN = "@appt.invalid"


def upgrade() -> None:
    op.execute(
        f"UPDATE appointment_calendar_emails "
        f"SET dummy_email = REPLACE(dummy_email, '{OLD_DOMAIN}', '{NEW_DOMAIN}') "
        f"WHERE dummy_email LIKE '%{OLD_DOMAIN}';"
    )


def downgrade() -> None:
    op.execute(
        f"UPDATE appointment_calendar_emails "
        f"SET dummy_email = REPLACE(dummy_email, '{NEW_DOMAIN}', '{OLD_DOMAIN}') "
        f"WHERE dummy_email LIKE '%{NEW_DOMAIN}';"
    )
