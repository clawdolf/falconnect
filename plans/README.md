# Plans

Scoped feature specs and future work for FalconConnect v3. Each file is a self-contained spec — read it, build it, move it to `done/` when shipped.

## Blocked (waiting on Seb)

- [falconverify-meta-pixel.md](falconverify-meta-pixel.md) — Site live, needs real Pixel ID
- [rachel-ai-sms.md](rachel-ai-sms.md) — Built, blocked on A2P 10DLC approval
- [ghl-token-refresh.md](ghl-token-refresh.md) — Expired token, manual refresh needed
- [voice-cloning.md](voice-cloning.md) — Seb needs to record 3-5 min natural speech
- GHL reply monitoring post-RVM — FC endpoint `POST /api/ghl/contact-declined` live (PR #3). Needs GHL workflow: inbound SMS trigger → keyword conditions (not interested, stop, don't want, etc.) → HTTP webhook to FC. Seb setting up in GHL tomorrow.

## Ready to Build

- [ghl-appointment-monitoring.md](ghl-appointment-monitoring.md) — GHL→Close+GCal sync when VA books appointment

## Queued

- FreeCallerRegistry daily script + spam monitoring integration (Call Confidence)

## Done

- GHL contact-declined webhook handler (PR #3, merged 2026-04-09) — POST /api/ghl/contact-declined. Catches post-RVM decline replies, sets Close cadence_stage to "0. declined", tags GHL, removes from workflows. Pending GHL workflow config.
