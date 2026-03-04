"""GHL → Notion webhook bridge — routes GHL events to Notion updates.

Handles multiple GHL event type naming conventions:
  appointment.booked / AppointmentCreate
  appointment.updated / AppointmentUpdate
  opportunity.stage_changed / OpportunityStageUpdate
  contact.opted_out / ContactOptOut
"""

import json
import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_session
from db.models import LeadXref, SyncLog
from models.webhook import GHLWebhookPayload
from services import notion
from utils.auth import verify_webhook_secret

logger = logging.getLogger("falconconnect.webhooks")

router = APIRouter()


def _normalize_event_type(raw_type: str) -> str:
    """Normalize GHL event types to a canonical form."""
    mapping = {
        "appointmentcreate": "appointment.booked",
        "appointment.booked": "appointment.booked",
        "appointmentupdate": "appointment.updated",
        "appointment.updated": "appointment.updated",
        "appointment.cancelled": "appointment.cancelled",
        "appointment.no_show": "appointment.no_show",
        "opportunitystageupdate": "opportunity.stage_changed",
        "opportunity.stage_changed": "opportunity.stage_changed",
        "contactoptout": "contact.opted_out",
        "contact.opted_out": "contact.opted_out",
    }
    return mapping.get(raw_type.lower().replace("-", "").replace("_", "").replace(" ", ""), raw_type)


@router.post("/ghl")
async def ghl_webhook(
    request: Request,
    _secret: str = Depends(verify_webhook_secret),
    session: AsyncSession = Depends(get_session),
):
    """Receive GHL webhook events and mirror changes to Notion.

    Verifies the shared secret header before processing.
    Routes events by type to the appropriate handler.
    Logs every sync event to the sync_log table.
    """
    raw_body = await request.json()
    payload = GHLWebhookPayload(**raw_body)
    event_type = _normalize_event_type(payload.type)

    logger.info("GHL webhook received: type=%s (normalized=%s) contactId=%s", payload.type, event_type, payload.contactId)

    # Route to handler
    handler = HANDLERS.get(event_type)
    if not handler:
        logger.info("Unhandled GHL event type: %s — logging and skipping", event_type)
        await _log_sync(
            session,
            event_type=event_type,
            source_id=payload.contactId,
            status="skipped",
            payload=raw_body,
        )
        return {"status": "skipped", "reason": f"unhandled event type: {event_type}"}

    # Look up the Notion page ID from our xref table
    notion_page_id = None
    if payload.contactId:
        result = await session.execute(
            select(LeadXref).where(LeadXref.ghl_contact_id == payload.contactId)
        )
        xref = result.scalar_one_or_none()
        if xref:
            notion_page_id = xref.notion_page_id

    if not notion_page_id:
        logger.warning(
            "No Notion page found for GHL contact %s — logging event without sync",
            payload.contactId,
        )
        await _log_sync(
            session,
            event_type=event_type,
            source_id=payload.contactId,
            status="no_xref",
            payload=raw_body,
        )
        return {"status": "no_xref", "contactId": payload.contactId}

    # Dispatch to handler
    try:
        await handler(payload, notion_page_id)
        await _log_sync(
            session,
            event_type=event_type,
            source_id=payload.contactId,
            target_id=notion_page_id,
            status="ok",
            payload=raw_body,
        )
        return {"status": "ok", "event": event_type, "notion_page_id": notion_page_id}

    except Exception as exc:
        logger.error("Webhook handler failed: %s — %s", event_type, exc)
        await _log_sync(
            session,
            event_type=event_type,
            source_id=payload.contactId,
            target_id=notion_page_id,
            status="error",
            error_detail=str(exc),
            payload=raw_body,
        )
        return {"status": "error", "detail": str(exc)}


# --- Event handlers ---

async def _handle_appointment_booked(payload: GHLWebhookPayload, notion_page_id: str):
    """Update Notion with appointment date and set status."""
    properties: dict = {
        "Lead Status": {"status": {"name": "Appointment Booked"}},
        "Opportunity Stage": {"status": {"name": "Appointment Scheduled"}},
    }
    if payload.startTime:
        properties["Appointment Date"] = {
            "date": {"start": payload.startTime}
        }
    await notion.update_page(notion_page_id, properties)
    logger.info("Appointment booked → Notion %s updated", notion_page_id)


async def _handle_appointment_updated(payload: GHLWebhookPayload, notion_page_id: str):
    """Update Notion appointment date if changed."""
    properties: dict = {}
    if payload.startTime:
        properties["Appointment Date"] = {
            "date": {"start": payload.startTime}
        }
    if payload.status:
        status_name = payload.status.lower()
        if "cancelled" in status_name or "canceled" in status_name:
            properties["Lead Status"] = {"status": {"name": "Not Interested/Lost"}}
        elif "no_show" in status_name or "noshow" in status_name:
            properties["Opportunity Stage"] = {"status": {"name": "No Show"}}
    if properties:
        await notion.update_page(notion_page_id, properties)
        logger.info("Appointment updated → Notion %s updated", notion_page_id)


async def _handle_appointment_cancelled(payload: GHLWebhookPayload, notion_page_id: str):
    """Clear appointment date and update status."""
    await notion.update_page(
        notion_page_id,
        {"Lead Status": {"status": {"name": "Not Interested/Lost"}}},
    )
    logger.info("Appointment cancelled → Notion %s updated", notion_page_id)


async def _handle_appointment_no_show(payload: GHLWebhookPayload, notion_page_id: str):
    """Mark the lead as no-show."""
    await notion.update_page(
        notion_page_id,
        {
            "Opportunity Stage": {"status": {"name": "No Show"}},
            "No Show Reachout": {"checkbox": True},
        },
    )
    logger.info("Appointment no-show → Notion %s updated", notion_page_id)


async def _handle_opportunity_stage_changed(payload: GHLWebhookPayload, notion_page_id: str):
    """Mirror the GHL pipeline stage to Notion Opportunity Stage."""
    stage = payload.stage or "Unknown"

    # Map GHL stage names to Notion Opportunity Stage options
    stage_map = {
        "New Lead": "Not Booked",
        "Have Not Reached": "Not Booked",
        "Booked Appointment": "Appointment Scheduled",
        "No Show Appointment": "No Show",
        "Semi-Interested": "Not Booked",
        "Callback/Follow Up": "Not Booked",
        "Not Interested": "Not Booked",
        "Presented": "Options Presented",
        "Underwriting/Submitted": "Application Submitted",
        "Approved": "Approved",
        "Issue Paid": "Approved",
    }

    # Find best match — strip emojis and match by prefix
    notion_stage = "Not Booked"
    stage_clean = stage.strip()
    for ghl_name, notion_name in stage_map.items():
        if ghl_name.lower() in stage_clean.lower():
            notion_stage = notion_name
            break

    await notion.update_page(
        notion_page_id,
        {"Opportunity Stage": {"status": {"name": notion_stage}}},
    )
    logger.info("Opportunity stage → %s → Notion %s (%s)", stage, notion_page_id, notion_stage)


async def _handle_contact_opted_out(payload: GHLWebhookPayload, notion_page_id: str):
    """Mark the lead as Invalid/DNC in Notion."""
    await notion.update_page(
        notion_page_id,
        {"Lead Status": {"status": {"name": "Invalid"}}},
    )
    logger.info("Contact opted out → Invalid → Notion %s", notion_page_id)


# Handler registry
HANDLERS = {
    "appointment.booked": _handle_appointment_booked,
    "appointment.updated": _handle_appointment_updated,
    "appointment.cancelled": _handle_appointment_cancelled,
    "appointment.no_show": _handle_appointment_no_show,
    "opportunity.stage_changed": _handle_opportunity_stage_changed,
    "contact.opted_out": _handle_contact_opted_out,
}


# --- Helpers ---

async def _log_sync(
    session: AsyncSession,
    event_type: str,
    source_id: str = None,
    target_id: str = None,
    status: str = "ok",
    error_detail: str = None,
    payload: dict = None,
):
    """Write a sync_log entry."""
    log = SyncLog(
        event_type=event_type,
        direction="ghl_to_notion",
        source_id=source_id or "",
        target_id=target_id or "",
        payload=json.dumps(payload, default=str) if payload else None,
        status=status,
        error_detail=error_detail,
    )
    session.add(log)
