"""iCal generation service — builds .ics feed from Notion appointment data.

Uses real Notion property names:
  Name (title), Mobile Phone (phone_number), Lead Status (status),
  LAge (select), Aggregate Comments (rich_text),
  Appointment Date (date), Follow-Up Date (date).
"""

import logging
from datetime import datetime, timedelta, date
from typing import Any, Dict, List

import pytz
from icalendar import Calendar, Event, Alarm

logger = logging.getLogger("falconconnect.calendar")

PHOENIX_TZ = pytz.timezone("America/Phoenix")


def build_ical_feed(events: List[Dict[str, Any]]) -> str:
    """Build a valid iCalendar string from Notion page results.

    Each event dict has an `_event_type` key: "appointment" or "followup".
    """
    cal = Calendar()
    cal.add("prodid", "-//FalconConnect v3//falconfinancial.org//")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "PUBLISH")
    cal.add("x-wr-calname", "FalconConnect — Seb")
    cal.add("x-wr-timezone", "America/Phoenix")

    seen_uids = set()

    for page in events:
        props = page.get("properties", {})
        page_id = page.get("id", "unknown")
        event_type = page.get("_event_type", "appointment")

        name = _title_text(props.get("Name", {}))
        phone = _phone(props.get("Mobile Phone", {}))
        lead_status = _status_text(props.get("Lead Status", {}))
        lage = _select_text(props.get("LAge", {}))
        comments = _rich_text(props.get("Aggregate Comments", {}))

        if event_type == "appointment":
            appt_date_str = _date_value(props.get("Appointment Date", {}))
            if not appt_date_str:
                continue

            uid = f"appt-{page_id}@falconconnect"
            if uid in seen_uids:
                continue
            seen_uids.add(uid)

            event = Event()
            event.add("uid", uid)
            summary = f"{name} — {phone}" if phone else name
            event.add("summary", summary)
            event.add("dtstart", _to_phoenix_dt(appt_date_str))
            event.add("duration", timedelta(hours=1))
            event.add(
                "description",
                f"Status: {lead_status or 'N/A'} | LAge: {lage or 'N/A'} | {comments or ''}".strip(),
            )
            event.add("dtstamp", datetime.now(PHOENIX_TZ))

            # 60-min reminder
            alarm60 = Alarm()
            alarm60.add("action", "DISPLAY")
            alarm60.add("trigger", timedelta(minutes=-60))
            alarm60.add("description", f"Appointment in 1 hour: {name}")
            event.add_component(alarm60)

            # 24-hour reminder
            alarm24 = Alarm()
            alarm24.add("action", "DISPLAY")
            alarm24.add("trigger", timedelta(hours=-24))
            alarm24.add("description", f"Appointment tomorrow: {name}")
            event.add_component(alarm24)

            cal.add_component(event)

        elif event_type == "followup":
            fu_date_str = _date_value(props.get("Follow Up Date", {}))
            if not fu_date_str:
                continue

            uid = f"followup-{page_id}@falconconnect"
            if uid in seen_uids:
                continue
            seen_uids.add(uid)

            event = Event()
            event.add("uid", uid)
            event.add("summary", f"Follow Up — {name}")

            fu_date = _parse_date_only(fu_date_str)
            if fu_date:
                event.add("dtstart", fu_date)  # all-day event (date, not datetime)
            else:
                event.add("dtstart", _to_phoenix_dt(fu_date_str))
                event.add("duration", timedelta(minutes=30))

            event.add("dtstamp", datetime.now(PHOENIX_TZ))

            # 8am morning reminder (for all-day events, TRIGGER is relative to start of day)
            alarm_morning = Alarm()
            alarm_morning.add("action", "DISPLAY")
            alarm_morning.add("trigger", timedelta(hours=8))  # 8am on the day
            alarm_morning.add("description", f"Follow up today: {name}")
            event.add_component(alarm_morning)

            cal.add_component(event)

    return cal.to_ical().decode("utf-8")


# --- Property extractors matching real Notion schema ---

def _title_text(prop: Dict[str, Any]) -> str:
    """Extract plain text from a Notion title property."""
    items = prop.get("title", [])
    if items:
        return "".join(item.get("plain_text", "") for item in items)
    return ""


def _rich_text(prop: Dict[str, Any]) -> str:
    """Extract plain text from a Notion rich_text property."""
    items = prop.get("rich_text", [])
    if items:
        return "".join(item.get("plain_text", "") for item in items)
    return ""


def _phone(prop: Dict[str, Any]) -> str:
    return prop.get("phone_number", "") or ""


def _status_text(prop: Dict[str, Any]) -> str:
    """Extract name from a Notion status property."""
    status = prop.get("status")
    if status:
        return status.get("name", "")
    return ""


def _select_text(prop: Dict[str, Any]) -> str:
    """Extract name from a Notion select property."""
    sel = prop.get("select")
    if sel:
        return sel.get("name", "")
    return ""


def _number_text(prop: Dict[str, Any]) -> str:
    val = prop.get("number")
    return str(val) if val is not None else ""


def _date_value(prop: Dict[str, Any]) -> str:
    """Extract the start date string from a Notion date property."""
    date_obj = prop.get("date")
    if date_obj:
        return date_obj.get("start", "")
    return ""


def _to_phoenix_dt(date_str: str) -> datetime:
    """Parse an ISO date/datetime string into a Phoenix-timezone datetime."""
    from dateutil import parser as dtparser

    dt = dtparser.parse(date_str)
    if dt.tzinfo is None:
        dt = PHOENIX_TZ.localize(dt)
    return dt.astimezone(PHOENIX_TZ)


def _parse_date_only(date_str: str):
    """If the string is a date-only (no time component), return a date object."""
    if len(date_str) == 10:  # YYYY-MM-DD
        try:
            return date.fromisoformat(date_str)
        except ValueError:
            pass
    return None
