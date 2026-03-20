"""Low-level Twilio REST API wrapper — httpx async, no SDK.

All Twilio API calls for the conference bridge go through this module.
"""

import logging
from base64 import b64encode
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import httpx

from config import get_settings

logger = logging.getLogger("falconconnect.twilio")

BASE_URL = "https://api.twilio.com/2010-04-01"


def _auth_header() -> Dict[str, str]:
    """Return HTTP Basic auth header for Twilio."""
    settings = get_settings()
    creds = f"{settings.twilio_account_sid}:{settings.twilio_auth_token}"
    encoded = b64encode(creds.encode()).decode()
    return {"Authorization": f"Basic {encoded}"}


def _account_url() -> str:
    settings = get_settings()
    return f"{BASE_URL}/Accounts/{settings.twilio_account_sid}"


async def create_participant(
    conference_name: str,
    to: str,
    from_: str,
    status_callback_url: str,
    twiml_url: str,
    label: str = "",
    early_media: bool = False,
    machine_detection: Optional[str] = None,
    timeout: int = 30,
) -> Dict[str, Any]:
    """Add a participant to a conference via Twilio Participants API.

    This creates the conference if it doesn't exist yet (first participant).
    Returns the participant resource dict from Twilio.
    """
    url = f"{_account_url()}/Conferences/{conference_name}/Participants.json"
    data = {
        "From": from_,
        "To": to,
        "Url": twiml_url,  # Required — TwiML to execute when participant answers (joins conference)
        "EarlyMedia": str(early_media).lower(),
        "StatusCallback": status_callback_url,
        "StatusCallbackEvent": "initiated ringing answered completed",
        "Timeout": str(timeout),
        "Label": label,
    }
    if machine_detection:
        data["MachineDetection"] = machine_detection

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, data=data, headers=_auth_header())
        if not resp.is_success:
            logger.error("Twilio error %s adding participant %s: %s", resp.status_code, label or to, resp.text)
        resp.raise_for_status()
        result = resp.json()
        logger.info("Added participant %s to conference %s: call_sid=%s",
                     label or to, conference_name, result.get("call_sid"))
        return result


async def update_participant(
    conference_sid: str,
    call_sid: str,
    *,
    muted: Optional[bool] = None,
    hold: Optional[bool] = None,
    hold_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Update a participant (mute/unmute/hold/unhold).

    Mute: POST to Calls resource (Participants Muted param is deprecated).
    Hold: POST to Participants resource — HoldUrl required on both hold AND unhold.
    """
    result = {}

    # Mute/unmute via Calls resource (Participants Muted is deprecated)
    if muted is not None:
        call_url = f"{_account_url()}/Calls/{call_sid}.json"
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(call_url, data={"Muted": str(muted).lower()}, headers=_auth_header())
            if not resp.is_success:
                logger.error("Twilio mute error %s: %s", resp.status_code, resp.text)
            resp.raise_for_status()
            result = resp.json()

    # Hold/unhold via Participants resource — HoldUrl required in both directions
    if hold is not None:
        part_url = f"{_account_url()}/Conferences/{conference_sid}/Participants/{call_sid}.json"
        data: Dict[str, str] = {"Hold": str(hold).lower()}
        # HoldUrl required whenever Hold param is present (Twilio requirement)
        data["HoldUrl"] = hold_url or "http://twimlets.com/holdmusic?Bucket=com.twilio.music.classical"
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(part_url, data=data, headers=_auth_header())
            if not resp.is_success:
                logger.error("Twilio hold error %s: %s", resp.status_code, resp.text)
            resp.raise_for_status()
            result = resp.json()

    return result


async def delete_participant(conference_sid: str, call_sid: str) -> None:
    """Remove a participant from a conference (hangs up their call)."""
    url = f"{_account_url()}/Conferences/{conference_sid}/Participants/{call_sid}.json"
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.delete(url, headers=_auth_header())
        resp.raise_for_status()
        logger.info("Removed participant %s from conference %s", call_sid, conference_sid)


async def get_conference(conference_sid: str) -> Dict[str, Any]:
    """Get conference resource by SID."""
    url = f"{_account_url()}/Conferences/{conference_sid}.json"
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, headers=_auth_header())
        resp.raise_for_status()
        return resp.json()


async def list_conference_participants(conference_sid: str) -> List[Dict[str, Any]]:
    """List all participants in a conference."""
    url = f"{_account_url()}/Conferences/{conference_sid}/Participants.json"
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, headers=_auth_header())
        resp.raise_for_status()
        data = resp.json()
        return data.get("participants", [])


async def end_conference(conference_sid: str) -> Dict[str, Any]:
    """End a conference by setting status to completed."""
    url = f"{_account_url()}/Conferences/{conference_sid}.json"
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(url, data={"Status": "completed"}, headers=_auth_header())
        resp.raise_for_status()
        return resp.json()


async def initiate_caller_id_verification(phone_number: str) -> Dict[str, Any]:
    """Start outgoing caller ID verification for a phone number.

    Twilio will call the number and play a 6-digit verification code.
    Returns the validation request resource with 'validation_code' (for testing)
    and 'call_sid'.
    """
    url = f"{_account_url()}/OutgoingCallerIds.json"
    data = {
        "PhoneNumber": phone_number,
        "FriendlyName": f"FC Bridge - {phone_number}",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, data=data, headers=_auth_header())
        resp.raise_for_status()
        result = resp.json()
        logger.info("Initiated caller ID verification for %s: call_sid=%s",
                     phone_number, result.get("call_sid"))
        return result


async def list_verified_caller_ids() -> List[Dict[str, Any]]:
    """List all verified outgoing caller IDs on the account."""
    url = f"{_account_url()}/OutgoingCallerIds.json?PageSize=50"
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, headers=_auth_header())
        resp.raise_for_status()
        data = resp.json()
        return data.get("outgoing_caller_ids", [])


async def get_call(call_sid: str) -> Dict[str, Any]:
    """Get a call resource by SID (for checking call status/duration)."""
    url = f"{_account_url()}/Calls/{call_sid}.json"
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, headers=_auth_header())
        resp.raise_for_status()
        return resp.json()
