"""Quo (OpenPhone) API integration — sync contacts after Notion/GHL import.

Pushes contact data with custom fields (State, Lender, Address) into Quo
so they are visible for dialing.
"""

import asyncio
import logging
from typing import Dict, Any, Optional

import httpx

logger = logging.getLogger("falconconnect.quo")

QUO_BASE = "https://api.openphone.com/v1"
QUO_API_KEY = "1kRWUvOQZkvGLfXeXA7xoQLJmc4j24Di"

# Custom field keys from Quo — maps Notion field names to Quo custom field keys
CUSTOM_FIELDS_MAP = {
    "State": "690bbacefd425c5afcd20b24",
    "Lender": "690bbaeffd425c5afcd20b2e",
    "Address": "690bbaf5fd425c5afcd20b37",
}


def _headers() -> Dict[str, str]:
    return {
        "Authorization": QUO_API_KEY,
        "Content-Type": "application/json",
    }


def _normalize_phone_e164(phone: str) -> str:
    """Normalize phone to E.164 format for Quo API."""
    digits = "".join(c for c in str(phone) if c.isdigit())
    if len(digits) == 10:
        return f"+1{digits}"
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    return f"+{digits}" if not phone.startswith("+") else phone


async def sync_contact(
    lead: Dict[str, Any],
    test_mode: bool = False,
) -> Optional[str]:
    """Sync a single contact to Quo after Notion/GHL import.

    Returns Quo contact ID on success, None on failure (non-fatal).
    """
    phone = lead.get("phone") or lead.get("mobile_phone")
    if not phone:
        logger.debug("Quo sync skipped — no phone for %s %s", lead.get("first_name"), lead.get("last_name"))
        return None

    first_name = lead.get("first_name", "")
    last_name = lead.get("last_name", "")

    # Build custom fields
    custom_fields = []
    if lead.get("state"):
        custom_fields.append({
            "key": CUSTOM_FIELDS_MAP["State"],
            "value": lead["state"],
        })
    if lead.get("lender"):
        custom_fields.append({
            "key": CUSTOM_FIELDS_MAP["Lender"],
            "value": lead["lender"],
        })
    if lead.get("address"):
        addr = lead["address"]
        if lead.get("city"):
            addr += f", {lead['city']}"
        if lead.get("state"):
            addr += f", {lead['state']}"
        if lead.get("zip_code"):
            addr += f" {lead['zip_code']}"
        custom_fields.append({
            "key": CUSTOM_FIELDS_MAP["Address"],
            "value": addr,
        })

    payload: Dict[str, Any] = {
        "firstName": first_name,
        "lastName": last_name,
        "phoneNumbers": [{"value": _normalize_phone_e164(phone)}],
    }

    if lead.get("email"):
        payload["emails"] = [{"value": lead["email"]}]

    if custom_fields:
        payload["customFields"] = custom_fields

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # Quo uses POST for create — check for existing by phone first
            resp = await client.post(
                f"{QUO_BASE}/contacts",
                headers=_headers(),
                json=payload,
            )

            if resp.status_code == 409:
                # Contact already exists — Quo returns conflict
                logger.info("Quo contact already exists for %s %s", first_name, last_name)
                return "exists"

            resp.raise_for_status()
            data = resp.json()
            contact_id = data.get("data", {}).get("id") or data.get("id", "")
            logger.info("Quo sync → %s %s → %s", first_name, last_name, contact_id)
            return contact_id

    except Exception as exc:
        logger.warning("Quo sync failed for %s %s (non-fatal): %s", first_name, last_name, exc)
        return None
