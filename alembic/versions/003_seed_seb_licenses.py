"""Seed Seb's 8 active insurance licenses (migrated from v2 prod DB).

NPN: 21408357
User ID: 72dc5b7c-ba2c-4a1d-83b9-733ff600c0d5

Revision ID: 003_seed_seb_licenses
Revises: 002_licenses
Create Date: 2026-03-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import String, Integer, Boolean
import datetime

# revision identifiers, used by Alembic.
revision = "003_seed_seb_licenses"
down_revision = "002_licenses"
branch_labels = None
depends_on = None

SEB_USER_ID = "72dc5b7c-ba2c-4a1d-83b9-733ff600c0d5"

LICENSES = [
    {
        "user_id": SEB_USER_ID,
        "state": "Arizona",
        "state_abbreviation": "AZ",
        "license_number": None,
        "verify_url": "https://sbs.naic.org/solar-external-lookup/lookup/licensee/summary/21408357?jurisdiction=AZ&entityType=IND&licenseType=PRO",
        "needs_manual_verification": False,
        "status": "active",
        "license_type": "insurance_producer",
    },
    {
        "user_id": SEB_USER_ID,
        "state": "Florida",
        "state_abbreviation": "FL",
        "license_number": "G258860",
        "verify_url": "https://licenseesearch.fldfs.com/Licensee/2700806",
        "needs_manual_verification": False,
        "status": "active",
        "license_type": "insurance_producer",
    },
    {
        "user_id": SEB_USER_ID,
        "state": "Kansas",
        "state_abbreviation": "KS",
        "license_number": None,
        "verify_url": "https://sbs.naic.org/solar-external-lookup/lookup/licensee/summary/21408357?jurisdiction=KS&entityType=IND&licenseType=PRO",
        "needs_manual_verification": False,
        "status": "active",
        "license_type": "insurance_producer",
    },
    {
        "user_id": SEB_USER_ID,
        "state": "Maine",
        "state_abbreviation": "ME",
        "license_number": None,
        "verify_url": "https://www.pfr.maine.gov/ALMSOnline/ALMSQuery/ShowDetail.aspx?DetailToken=704F3C701A9F11E086BB0F98AA047C448C67C5003D086308CD98C8424EC1769E",
        "needs_manual_verification": False,
        "status": "active",
        "license_type": "insurance_producer",
    },
    {
        "user_id": SEB_USER_ID,
        "state": "North Carolina",
        "state_abbreviation": "NC",
        "license_number": None,
        "verify_url": "https://sbs.naic.org/solar-external-lookup/lookup/licensee/summary/21408357?jurisdiction=NC&entityType=IND&licenseType=PRO",
        "needs_manual_verification": False,
        "status": "active",
        "license_type": "insurance_producer",
    },
    {
        "user_id": SEB_USER_ID,
        "state": "Oregon",
        "state_abbreviation": "OR",
        "license_number": None,
        "verify_url": "https://sbs.naic.org/solar-external-lookup/lookup/licensee/summary/21408357?jurisdiction=OR&entityType=IND&licenseType=PRO",
        "needs_manual_verification": False,
        "status": "active",
        "license_type": "insurance_producer",
    },
    {
        "user_id": SEB_USER_ID,
        "state": "Pennsylvania",
        "state_abbreviation": "PA",
        "license_number": "1152553",
        "verify_url": "https://www.sircon.com/ComplianceExpress/Inquiry/consumerInquiry.do?nonSscrb=Y",
        "needs_manual_verification": True,
        "status": "active",
        "license_type": "insurance_producer",
    },
    {
        "user_id": SEB_USER_ID,
        "state": "Texas",
        "state_abbreviation": "TX",
        "license_number": "3317972",
        "verify_url": "https://www.sircon.com/ComplianceExpress/Inquiry/consumerInquiry.do?nonSscrb=Y",
        "needs_manual_verification": True,
        "status": "active",
        "license_type": "insurance_producer",
    },
]


def upgrade() -> None:
    bind = op.get_bind()
    # Insert only if not already present (idempotent)
    for lic in LICENSES:
        result = bind.execute(
            sa.text(
                "SELECT COUNT(*) FROM licenses WHERE user_id = :uid AND state_abbreviation = :abbr"
            ),
            {"uid": lic["user_id"], "abbr": lic["state_abbreviation"]},
        )
        if result.scalar() == 0:
            bind.execute(
                sa.text(
                    """
                    INSERT INTO licenses
                        (user_id, state, state_abbreviation, license_number, verify_url,
                         needs_manual_verification, status, license_type, created_at, updated_at)
                    VALUES
                        (:user_id, :state, :state_abbreviation, :license_number, :verify_url,
                         :needs_manual_verification, :status, :license_type, NOW(), NOW())
                    """
                ),
                lic,
            )


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text("DELETE FROM licenses WHERE user_id = :uid"),
        {"uid": SEB_USER_ID},
    )
