"""iCal feed endpoints — appointments and follow-ups via Google Calendar.

/api/calendar/appointments.ics — timed appointment events only
/api/calendar/followups.ics    — all-day follow-up events only

Both secured by the same CALENDAR_SECRET query param.

NOTE: These endpoints previously sourced data from Notion (deprecated 2026-03-29).
They now return empty feeds. GCal is the canonical calendar source — iCal feeds
can be rebuilt from GCal data if needed.
"""

import logging

from fastapi import APIRouter, Query, Response

from services.calendar import build_appointments_feed, build_followups_feed
from utils.auth import verify_calendar_token

logger = logging.getLogger("falconconnect.calendar")

router = APIRouter()


@router.get("/appointments.ics")
async def appointments_feed(token: str = Query(..., description="Calendar feed secret token")):
    """iCal feed of upcoming appointments.

    NOTE: Notion data source removed (2026-03-29). Returns empty feed.
    Use Google Calendar directly for appointment data.
    """
    verify_calendar_token(token)

    # Notion was the data source — now deprecated. Return empty feed.
    logger.info("Appointments feed requested — returning empty (Notion removed)")
    return Response(
        content=build_appointments_feed([]),
        media_type="text/calendar",
        headers={
            "Content-Disposition": "inline; filename=appointments.ics",
            "Cache-Control": "no-cache, no-store, must-revalidate",
        },
    )


@router.get("/followups.ics")
async def followups_feed(token: str = Query(..., description="Calendar feed secret token")):
    """iCal feed of upcoming follow-ups.

    NOTE: Notion data source removed (2026-03-29). Returns empty feed.
    Use Google Calendar directly for follow-up data.
    """
    verify_calendar_token(token)

    # Notion was the data source — now deprecated. Return empty feed.
    logger.info("Follow-ups feed requested — returning empty (Notion removed)")
    return Response(
        content=build_followups_feed([]),
        media_type="text/calendar",
        headers={
            "Content-Disposition": "inline; filename=followups.ics",
            "Cache-Control": "no-cache, no-store, must-revalidate",
        },
    )
