"""Re-seed licenses — 003 ran but op.get_bind() returned no rows (async context issue).
This migration uses the correct op.execute() pattern for async alembic.

Revision ID: 004_reseed_licenses
Revises: 003_seed_seb_licenses
Create Date: 2026-03-04
"""
from alembic import op
import sqlalchemy as sa

revision = "004_reseed_licenses"
down_revision = "003_seed_seb_licenses"
branch_labels = None
depends_on = None

SEB_USER_ID = "72dc5b7c-ba2c-4a1d-83b9-733ff600c0d5"

LICENSES = [
    ("Arizona",       "AZ", None,       "https://sbs.naic.org/solar-external-lookup/lookup/licensee/summary/21408357?jurisdiction=AZ&entityType=IND&licenseType=PRO", False),
    ("Florida",       "FL", "G258860",  "https://licenseesearch.fldfs.com/Licensee/2700806",                                                                          False),
    ("Kansas",        "KS", None,       "https://sbs.naic.org/solar-external-lookup/lookup/licensee/summary/21408357?jurisdiction=KS&entityType=IND&licenseType=PRO", False),
    ("Maine",         "ME", None,       "https://www.pfr.maine.gov/ALMSOnline/ALMSQuery/ShowDetail.aspx?DetailToken=704F3C701A9F11E086BB0F98AA047C448C67C5003D086308CD98C8424EC1769E", False),
    ("North Carolina","NC", None,       "https://sbs.naic.org/solar-external-lookup/lookup/licensee/summary/21408357?jurisdiction=NC&entityType=IND&licenseType=PRO", False),
    ("Oregon",        "OR", None,       "https://sbs.naic.org/solar-external-lookup/lookup/licensee/summary/21408357?jurisdiction=OR&entityType=IND&licenseType=PRO", False),
    ("Pennsylvania",  "PA", "1152553",  "https://www.sircon.com/ComplianceExpress/Inquiry/consumerInquiry.do?nonSscrb=Y",                                             True),
    ("Texas",         "TX", "3317972",  "https://www.sircon.com/ComplianceExpress/Inquiry/consumerInquiry.do?nonSscrb=Y",                                             True),
]


def upgrade() -> None:
    # op.execute() works correctly in async alembic run_sync context
    for state, abbr, lic_num, verify_url, manual in LICENSES:
        # Idempotent: skip if already present
        op.execute(
            sa.text(
                "INSERT INTO licenses "
                "(user_id, state, state_abbreviation, license_number, verify_url, "
                "needs_manual_verification, status, license_type, created_at, updated_at) "
                "SELECT :uid, :state, :abbr, :lic_num, :verify_url, :manual, 'active', "
                "'insurance_producer', NOW(), NOW() "
                "WHERE NOT EXISTS ("
                "  SELECT 1 FROM licenses "
                "  WHERE user_id = :uid AND state_abbreviation = :abbr"
                ")"
            ).bindparams(
                uid=SEB_USER_ID,
                state=state,
                abbr=abbr,
                lic_num=lic_num,
                verify_url=verify_url,
                manual=manual,
            )
        )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM licenses WHERE user_id = :uid").bindparams(uid=SEB_USER_ID)
    )
