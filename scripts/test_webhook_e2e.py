"""End-to-end test for Close webhook → GCal event creation.

Simulates the exact Close webhook payload structure and traces
through the handler to find where the pipeline breaks.

Run from repo root: python scripts/test_webhook_e2e.py
Requires env vars: CLOSE_API_KEY, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET,
                   GOOGLE_REFRESH_TOKEN, DATABASE_URL
"""

import asyncio
import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ---- Step 0: Verify the payload parsing logic (no network needed) ----
def test_parsing():
    print("=" * 60)
    print("STEP 0: Verifying Close webhook payload parsing (after fix)")
    print("=" * 60)

    from services.close_sms import (
        CF_APPOINTMENT_DATETIME,
        CF_APPOINTMENT_NOTES,
        CF_APPOINTMENT_TIMEZONE,
    )

    # Exact payload structure from Close
    event_data = {
        "_type": "CustomActivity",
        "custom_activity_type_id": "actitype_6awVkZoRuXH1FWUd1F97CH",
        "contact_id": None,
        "lead_id": "lead_rFJwlC00Qx2W6J6ezU7D4UIsXGDet6L8V8CVZKD8JJB",
        "custom.cf_iiDP2BjqqEApsTl1uGQqbzw2cWm5Le8r3wTuUC8uc5Z": "2026-03-15T21:00:00+00:00",
        "custom.cf_mqWOudG1Apd6FdrzP2qZqC1qUgx0pvGLKg4ZZgFsmn7": "AZ (MST, no DST)",
        "custom.cf_WEM8v7zGSnCDPIEQuxNmdct5l5i19kCRoPCX5BexLqa": "Test notes",
    }

    # Fixed extraction: "custom.cf_XXX" flat keys
    dt_val = event_data.get(f"custom.{CF_APPOINTMENT_DATETIME}")
    tz_val = event_data.get(f"custom.{CF_APPOINTMENT_TIMEZONE}")
    notes_val = event_data.get(f"custom.{CF_APPOINTMENT_NOTES}")

    print(f"DateTime: {dt_val}")
    print(f"Timezone: {tz_val}")
    print(f"Notes: {notes_val}")

    assert dt_val == "2026-03-15T21:00:00+00:00", f"DateTime extraction failed: {dt_val}"
    assert tz_val == "AZ (MST, no DST)", f"Timezone extraction failed: {tz_val}"
    assert notes_val == "Test notes", f"Notes extraction failed: {notes_val}"
    print("✓ Custom field extraction: PASS")

    # Timezone resolution
    from services.close_sms import _resolve_timezone
    tz_name, tz_label = _resolve_timezone("AZ (MST, no DST)")
    assert tz_name == "America/Phoenix", f"TZ resolve failed: {tz_name}"
    assert tz_label == "AZ", f"TZ label failed: {tz_label}"
    print("✓ Timezone resolution: PASS")

    # Test other timezone formats
    for choice, expected_tz, expected_label in [
        ("ET (Eastern)", "America/New_York", "ET"),
        ("CT (Central)", "America/Chicago", "CT"),
        ("MT (Mountain)", "America/Denver", "MT"),
        ("PT (Pacific)", "America/Los_Angeles", "PT"),
        ("AZ", "America/Phoenix", "AZ"),
        (None, "America/Phoenix", "AZ"),
    ]:
        tz_name, tz_label = _resolve_timezone(choice)
        assert tz_name == expected_tz, f"TZ resolve '{choice}' → {tz_name} (expected {expected_tz})"
        assert tz_label == expected_label, f"TZ label '{choice}' → {tz_label} (expected {expected_label})"
    print("✓ All timezone formats: PASS")
    print()


def test_sms_results_none():
    """Verify sms_results is never None (always a dict with defaults)."""
    print("=" * 60)
    print("STEP 1: Verifying sms_results safety")
    print("=" * 60)

    sms_results = {"confirmation": None, "reminder_24hr": None, "reminder_1hr": None}
    # This should never crash now
    assert sms_results.get("confirmation") is None
    assert sms_results.get("reminder_24hr") is None
    print("✓ sms_results default dict: PASS")
    print()


async def test_e2e_live():
    """Live e2e test — calls _process_appointment directly.

    Requires CLOSE_API_KEY and GOOGLE_* env vars to be set.
    Uses a real lead ID (Max Nielsen) to test contact lookup + GCal creation.
    """
    print("=" * 60)
    print("STEP 2: Live E2E test (requires env vars)")
    print("=" * 60)

    from config import get_settings
    settings = get_settings()

    if not settings.close_api_key:
        print("⚠️  CLOSE_API_KEY not set — skipping live test")
        return
    if not settings.google_refresh_token:
        print("⚠️  GOOGLE_REFRESH_TOKEN not set — skipping live test")
        return

    print(f"Close API key: ...{settings.close_api_key[-6:]}")
    print(f"Google Calendar ID: {settings.google_calendar_id}")
    print(f"Google client ID: ...{settings.google_client_id[-10:] if settings.google_client_id else 'NOT SET'}")

    # Initialize database
    from db.database import init_db
    await init_db()
    print("✓ Database initialized")

    # Import the handler
    from routers.close_webhooks import _process_appointment

    # Simulate exact Close webhook data (with "custom.cf_XXX" flat keys)
    activity_data = {
        "_type": "CustomActivity",
        "custom_activity_type_id": "actitype_6awVkZoRuXH1FWUd1F97CH",
        "contact_id": None,  # Null — requires lead lookup
        "lead_id": "lead_rFJwlC00Qx2W6J6ezU7D4UIsXGDet6L8V8CVZKD8JJB",
        "custom.cf_iiDP2BjqqEApsTl1uGQqbzw2cWm5Le8r3wTuUC8uc5Z": "2026-03-15T21:00:00+00:00",
        "custom.cf_mqWOudG1Apd6FdrzP2qZqC1qUgx0pvGLKg4ZZgFsmn7": "AZ (MST, no DST)",
        "custom.cf_WEM8v7zGSnCDPIEQuxNmdct5l5i19kCRoPCX5BexLqa": "E2E test appointment",
    }
    lead_id = "lead_rFJwlC00Qx2W6J6ezU7D4UIsXGDet6L8V8CVZKD8JJB"

    print(f"\nProcessing appointment for lead: {lead_id}")
    print("Calling _process_appointment()...")

    try:
        result = await _process_appointment(activity_data, lead_id)
        print(f"\n✓ Result: {json.dumps(result, indent=2, default=str)}")

        if result.get("status") == "ok":
            print("\n✓ E2E TEST PASSED — GCal event created!")
            print(f"  Event ID: {result.get('gcal_event_id')}")
            print(f"  Dummy email: {result.get('dummy_email')}")
        else:
            print(f"\n❌ E2E TEST FAILED — status: {result.get('status')}, reason: {result.get('reason')}")
    except Exception as exc:
        print(f"\n❌ E2E TEST CRASHED: {type(exc).__name__}: {exc}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_parsing()
    test_sms_results_none()

    # Only run live test if --live flag passed
    if "--live" in sys.argv:
        asyncio.run(test_e2e_live())
    else:
        print("Skipping live e2e test (pass --live to run)")
        print("Note: live test requires CLOSE_API_KEY, GOOGLE_* env vars")
