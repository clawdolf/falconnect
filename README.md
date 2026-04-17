# FalconConnect v3

Lead sanitization engine and webhook middleware for **Falcon Financial**. Ingests leads from multiple vendors, normalizes/deduplicates them, pushes to **Close.com** (primary CRM), and bridges webhooks between Close, GoHighLevel, Notion, and Google Calendar.

## Architecture

```
┌─────────────┐     ┌─────────────────────────────┐     ┌────────────┐
│  React SPA  │────▶│  FastAPI backend (Render)    │────▶│ Close.com  │
│  (Vite)     │     │  PostgreSQL (asyncpg)        │     │ GHL        │
└─────────────┘     │  Alembic migrations          │     │ Notion     │
                    │  Clerk auth                   │     │ Google Cal │
                    └─────────────────────────────┘     └────────────┘
```

- **Backend**: Python / FastAPI, async throughout, deployed on Render
- **Frontend**: React (Vite), Clerk auth, served as static build
- **Database**: PostgreSQL via SQLAlchemy async + Alembic migrations
- **Integrations**: Close.com, GoHighLevel, Notion, Google Calendar, Clerk

## Local Setup

```bash
# Clone & install
git clone <repo-url>
cd falconconnect-v3
pip install -r requirements.txt

# Frontend
cd frontend && npm install && npm run dev

# Environment
cp .env.example .env
# Fill in API keys (see below)

# Run backend (dev)
uvicorn main:app --reload --port 8000

# Run migrations (production)
alembic upgrade head
```

## Environment Variables

### Required

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (`postgresql+asyncpg://...`) |
| `CLERK_PUBLISHABLE_KEY` | Clerk frontend auth key |
| `CLERK_SECRET_KEY` | Clerk backend auth key |
| `CLOSE_API_KEY` | Close.com API key |
| `CLOSE_WEBHOOK_SECRET` | Shared secret for Close webhook verification |
| `CLOSE_SMS_FROM_NUMBER` | Outbound SMS number for Close |
| `CLOSE_APPOINTMENT_ACTIVITY_TYPE_ID` | Close custom activity type for appointments |

### Integration Keys

| Variable | Description |
|----------|-------------|
| `GHL_API_KEY` | GoHighLevel private integration API key |
| `GHL_LOCATION_ID` | GHL location/sub-account ID |
| `GHL_WEBHOOK_SECRET` | GHL webhook verification secret |
| `GHL_CALENDAR_ID` | GHL calendar ID for appointment booking |
| `NOTION_TOKEN` | Notion integration token |
| `NOTION_LEADS_DB_ID` | Notion leads database ID |
| `CALENDAR_SECRET` | Secret token for iCal feed URLs |
| `QUO_API_KEY` | Quo (OpenPhone) API key |

### Google Calendar (Service Account)

| Variable | Description |
|----------|-------------|
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Service account credentials JSON |
| `GOOGLE_CALENDAR_ID` | Calendar ID (default: `primary`) |
| `GOOGLE_CLIENT_ID` | OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | OAuth client secret |
| `GOOGLE_REFRESH_TOKEN` | OAuth refresh token |

### Notion → GHL Sync

| Variable | Default | Description |
|----------|---------|-------------|
| `NOTION_GHL_SYNC_ENABLED` | `true` | Master on/off switch |
| `NOTION_GHL_SYNC_DRY_RUN` | `true` | Log-only mode (no GHL writes) |
| `NOTION_GHL_SYNC_AFTER_DATE` | `2026-03-03` | Only sync appointments after this date |
| `NOTION_GHL_SYNC_INTERVAL` | `300` | Seconds between sync polls |

## API Overview

| Router file | Prefix | Purpose |
|-------------|--------|---------|
| `routers/leads.py` | `/api/leads` | Lead capture & bulk CSV import to Close.com |
| `routers/ad_leads.py` | `/api/ad-leads` | Ad-sourced lead ingestion |
| `routers/webhooks.py` | `/api/webhooks` | GHL webhook receiver → Notion sync |
| `routers/close_webhooks.py` | `/api/close-webhooks` | Close.com webhook handler (appointments, SMS reminders, GCal) |
| `routers/calendar.py` | `/api/calendar` | iCal feeds (appointments + follow-ups) |
| `routers/analytics.py` | `/api/analytics` | Daily production metrics |
| `routers/campaigns.py` | `/api/campaigns` | Ad campaign management |
| `routers/research.py` | `/api/research` | Research engine dashboard (hypotheses, ads, cycles) |
| `routers/agents.py` | `/api/agents` | Agent profile management (FalconVerify) |
| `routers/licenses.py` | `/api/licenses` | Agent license records |
| `routers/sms_templates.py` | `/api/sms-templates` | Editable SMS reminder templates |
| `routers/sheets.py` | `/api/sheets` | Google Sheets integration |
| `routers/sync.py` | `/api/sync` | Research cycle sync (Mac Mini → PostgreSQL) |
| `routers/admin.py` | `/api/admin` | Health checks, version info |

## Deployment

Deployed on **Render** (service ID: `srv-d69n3c8gjchc73dkq2d0`).

- Push to `main` triggers auto-deploy
- Database: Render-managed PostgreSQL
- Migrations run via `alembic upgrade head` on deploy
- Frontend built as static site, served separately

## Close.com Integration Notes

- **Primary CRM** — all leads ultimately land in Close
- Bulk import writes leads directly via Close API (`routers/leads.py`)
- Close webhooks (`routers/close_webhooks.py`) handle:
  - Appointment creation → SMS confirmation + 24hr/1hr reminders
  - Google Calendar event sync (bidirectional)
  - Lead status changes
- SMS sent via Close's built-in SMS with phone number pool for area-code matching
- Appointment reminders tracked in `appointment_reminders` table

## Operations

### Auth fail-closed

If `CLERK_SECRET_KEY` is missing from Render the service **crashes at startup**
rather than silently disabling auth. To run locally without Clerk, set
`ALLOW_NO_AUTH=true` in `.env` — never set this on Render.

### Rate limiting

Public endpoints are rate-limited via `slowapi`. Limits are defined per-route;
see `utils/rate_limit.py` for the key function (prefers `CF-Connecting-IP`).
429 responses are expected for abuse traffic — not an incident.

### Bot protection

Public ad landing pages run Cloudflare Turnstile. The backend verifies tokens
server-side; if `TURNSTILE_SECRET` is unset, verification is skipped (rollout
coordination mode). **Deploy order**: set `VITE_TURNSTILE_SITEKEY` on
Cloudflare Pages first, then `TURNSTILE_SECRET` on Render — reversing this
order will reject legitimate form submissions.

### Observability

- `SENTRY_DSN` (backend) / `VITE_SENTRY_DSN` (frontend) — unset = no-op
- Production logs are JSON (enable with `RENDER=true` or `ENVIRONMENT=production`)
- Auth failures: search logs for `"event":"auth_failed"`
- Rate-limit hits: slowapi logs `ratelimit X per Y exceeded at endpoint …`

### Webhook secret rotation

Rotate `CLOSE_WEBHOOK_SECRET` / `GHL_WEBHOOK_SECRET` if leaked:

```bash
python -c "import secrets; print(secrets.token_hex(32))"  # 64-char hex
```

1. Set the new value in Render env and redeploy.
2. Update the matching value in Close Developer → Webhook / GHL Settings → Integrations.
3. Expect a short window (~5 min) where one side has the old secret and the
   other has the new — webhooks will fail signature verification in that gap.

### Mac Mini research poller

`~/Library/LaunchAgents/com.falcon.trigger-poller.plist` polls
`/api/research/triggers/pending` every 300s using `X-Loop-Token`. The token
value must match `LOOP_SERVICE_TOKEN` in Render env. If you rotate it,
update both sides before restarting the LaunchAgent:

```bash
launchctl unload ~/Library/LaunchAgents/com.falcon.trigger-poller.plist
launchctl load ~/Library/LaunchAgents/com.falcon.trigger-poller.plist
```

### Production doc routes

`/docs`, `/redoc`, and `/openapi.json` return 404 in production
(`RENDER=true` or `ENVIRONMENT=production`). Locally they are reachable.

---

*Falcon Financial — Seb Taillieu*
