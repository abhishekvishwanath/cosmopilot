# API Conventions — Phase 0

Group structure is fixed by CLAUDE.md §28. This document defines the conventions applied across all of them, decided in Phase 0 so every phase from Phase 1 onward implements endpoints consistently instead of improvising per-feature.

## Route groups (CLAUDE.md §28)

```text
/api/v1/auth
/api/v1/clinics
/api/v1/doctors
/api/v1/treatments
/api/v1/leads
/api/v1/conversations
/api/v1/messages
/api/v1/appointments
/api/v1/analytics
/api/v1/knowledge
/api/v1/integrations
/api/v1/webhooks
```

One FastAPI router module per group, mounted under `/api/v1`. Versioning is in the URL path (not a header) so it's visible in logs, docs, and n8n webhook configs without extra inspection.

## Public vs authenticated endpoints

Two classes only, kept clearly separate:

- **Public** (no auth): the enquiry/lead form submission endpoint, and provider webhooks (`/api/v1/webhooks/*`) which authenticate via signature verification instead of a session. Public endpoints are minimal by design (CLAUDE.md §28) and rate-limited.
- **Authenticated** (clinic staff / admin): everything else — `clinics`, `doctors`, `treatments` (write), `leads` (read/manage), `conversations`, `appointments` (admin actions), `analytics`, `knowledge`, `integrations`. Uses Supabase Auth JWT, validated in FastAPI middleware/dependency, with clinic-scoped authorization enforced on every query (CLAUDE.md §23).

Read-only public endpoints (e.g. published treatment info for the landing page) are separated from admin endpoints even within the same resource group, e.g. `GET /api/v1/treatments/{slug}` (public) vs `GET /api/v1/treatments` admin list with unpublished/internal fields (authenticated).

## Request/response conventions

- All request/response bodies are typed Pydantic schemas (`app/schemas/`), never raw dicts.
- Timestamps: ISO 8601 UTC (`...Z`) on the wire; stored as `timestamptz` in Postgres.
- IDs: UUIDs as strings on the wire.
- Pagination: cursor-based (`?cursor=...&limit=...`) for list endpoints expected to grow unbounded (`leads`, `messages`, `events`); offset-based is acceptable for small, bounded lists (`doctors`, `treatments` per clinic).
- Partial updates: `PATCH` with only the fields being changed; `PUT` is not used.

## Error format

Every error response uses one consistent shape:

```json
{
  "error": {
    "code": "lead_not_found",
    "message": "Human-readable explanation, safe to show to a developer.",
    "details": {}
  }
}
```

- `code`: stable, machine-readable, snake_case — safe to branch on in frontend/n8n.
- `message`: for logs/debugging, not necessarily shown to end patients.
- HTTP status code carries the actual semantics (400/401/403/404/409/422/429/500); `code` disambiguates within that status.
- Validation errors (422) use FastAPI/Pydantic's default detail structure nested under `details`.

Patient-facing error copy (e.g. what the AI concierge says on a calendar failure) is defined in the service/agent layer, not derived from this API error format — see CLAUDE.md §25 for the required graceful-fallback wording.

## Idempotency

- All webhook endpoints (`/api/v1/webhooks/*`) require an idempotency key sourced from the provider's own event ID (Vapi call ID, Meta message ID, Stripe event ID) — see CLAUDE.md §24. Duplicate events return `200` without reprocessing.
- Mutating admin endpoints that trigger external side effects (e.g. "book appointment", "send WhatsApp") accept an optional client-supplied `Idempotency-Key` header, stored and checked the same way, to protect against double-submission from the frontend (double-click, retry-on-timeout).

## Authorization enforcement

Every authenticated route depends on a shared `get_current_clinic_user` dependency that resolves the caller's `clinic_id` from their session — every repository/service call for that request is scoped to that `clinic_id`. No endpoint accepts a client-supplied `clinic_id` for authorization purposes (it may appear in a URL for readability, but the resolved session clinic is what's actually checked against).

## Rate limiting

- Public endpoints: strict per-IP limits (enquiry form, public read endpoints).
- Webhook endpoints: limited by signature-verified provider traffic patterns, not raw IP (a legitimate provider can burst).
- Authenticated endpoints: generous per-clinic-user limits, mainly to catch runaway loops (e.g. a misconfigured n8n workflow), not normal staff usage.

Exact limits are tuned in Phase 12 (Production Hardening); Phase 1 stands up the rate-limiting middleware with conservative defaults so it's not bolted on later.

## Logging

Every request logs: route, clinic_id (if resolved), status code, latency, and — for tool/webhook endpoints — the provider event ID. AI tool-call endpoints additionally log which tool was invoked and a redacted view of its arguments (never full patient PII in plain log lines beyond what's already in the DB).

## What Phase 0 does NOT do

- No FastAPI app or routers exist yet — this document is the contract Phase 1+ implements against.
- No auth implementation yet (Phase 1 lays the foundation; RLS + full clinic isolation hardened in Phase 12).
- No rate-limiting middleware code yet.
