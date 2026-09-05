# Database Plan — Phase 0

Schema authority is CLAUDE.md §8. This document is the Phase 0 plan for turning that into real Postgres migrations in Phase 2 — table implementation, key relationships, and conventions. No migrations are created yet.

## Conventions (applied to every table)

- `id`: UUID primary key (`gen_random_uuid()` / `uuid_generate_v4()`).
- `created_at` / `updated_at`: `timestamptz`, defaulted server-side, `updated_at` maintained via trigger.
- Every clinic-scoped table has a `clinic_id` foreign key to `clinics.id` — this is the basis for **clinic-scoped authorization** (CLAUDE.md §23). Row-level security (RLS) policies will enforce this at the Postgres layer, not just in application code.
- Enum-like fields (`status`, lead states, etc.) use Postgres `enum` types or `text` + `CHECK` constraint — decided per-table in Phase 2 based on how often values need to change.
- Soft deletes are not assumed by default; use them only where CLAUDE.md's data-deletion/export requirements (§23) need history preserved.

## Entities and relationships

```text
clinics 1───* clinic_locations
clinics 1───* doctors
clinics 1───* treatments
clinics 1───* leads
clinics 1───* visitor_sessions
clinics 1───* conversations
clinics 1───* appointments
clinics 1───* documents
clinics 1───* integrations
clinics 1───* events
clinics 1───* payments

leads 1───* consents
leads 1───* conversations
leads 1───* appointments
leads 1───1..* visitor_sessions (attribution)

conversations 1───* messages

appointments 1───* appointment_events
appointments 1───0..1 payments

doctors *───* treatments (a doctor can perform many treatments; a treatment can be offered by many doctors) — junction table TBD in Phase 2 if needed, or treatments.doctor_id kept simple for v1 depending on clinic reality
```

## Table-by-table notes (implementation detail beyond CLAUDE.md §8's field list)

### `clinics`
- `status`: `active | inactive | onboarding`.
- `settings`: `jsonb` — clinic-level config (follow-up timing, WhatsApp opt-in copy, etc.) so new config doesn't require a migration.

### `leads`
- `status`: the lead state machine from CLAUDE.md §9 — implemented as a Postgres enum so transitions are constrained at the DB layer, not just in app code (belt-and-suspenders with the service-layer state machine).
- `consent`: boolean summary column; full consent history lives in `consents`.
- `source` / `landing_page`: preserved verbatim from `visitor_sessions` at lead-creation time for durable attribution even if the session record is later pruned.

### `visitor_sessions`
- `anonymous_id`: client-generated ID (cookie), used to stitch a visit to a later form submission before a `lead_id` exists.

### `conversations`
- `channel`: `voice | whatsapp`.
- `external_id`: Vapi call ID or WhatsApp conversation/thread ID — used for webhook idempotency lookups.
- `summary`: structured summary only (CLAUDE.md §23 — avoid storing raw sensitive conversation content when a summary suffices). Raw transcript, if retained at all, goes to Supabase Storage with restricted access, not this column.

### `messages`
- `direction`: `inbound | outbound`.
- `sender_type`: `patient | ai | staff`.
- `external_id`: provider message ID, used for webhook dedup.

### `appointments`
- `status`: `pending | booked | confirmed | cancelled | completed | no_show` (aligned with the lead state machine but appointment-specific).
- `external_id`: ID from the `CalendarProvider` in use (mock UUID in demo mode, real provider ID in production) — this is what makes the provider swappable without changing this table.

### `appointment_events`
- Append-only audit trail (booked, rescheduled, cancelled, reminder sent, no-show marked) — this is what powers the CRM timeline (CLAUDE.md §19).

### `consents`
- One row per consent grant/revocation event (not a single mutable flag) so opt-outs are auditable per channel.

### `payments`
- Only populated if/when Stripe integration is actually enabled for a clinic (CLAUDE.md §2 — payment processor is out of scope until needed). No card data ever stored here — `provider` + `external_id` + `payment_link` only.

### `documents`
- Backs the RAG pipeline (CLAUDE.md §11). `embedding_status`: `pending | processing | ready | failed`. Actual vectors live in a separate `document_chunks` (or similar) table with a `pgvector` column, added in Phase 5 when the knowledge base is built — not listed in CLAUDE.md §8's top-level list because it's an implementation detail of the RAG pipeline, not a CRM entity.

### `integrations`
- One row per clinic per provider type (`voice`, `whatsapp`, `calendar`, `payments`, `email`), tracking connection `status` and last `health_check` — this is what lets the CRM show "WhatsApp: mocked" vs "WhatsApp: connected" per CLAUDE.md §26.

### `events`
- Generic funnel/analytics event log (CLAUDE.md §22) — every funnel stage transition writes here in addition to any entity-specific state change, so analytics never has to reconstruct history from other tables.

## Row-Level Security (RLS)

Every clinic-scoped table gets an RLS policy keyed on `clinic_id` matching the authenticated user's clinic (via Supabase Auth JWT claims), built in Phase 1 (auth foundation) and applied per-table as each table is created in Phase 2. This is the DB-layer half of "clinic-scoped authorization" (CLAUDE.md §23) — the API layer enforces it too, but RLS is the backstop.

## Indexing (initial, revisited as real usage patterns emerge)

- `leads(clinic_id, status)` — CRM dashboard filters.
- `leads(clinic_id, created_at desc)` — recent leads list.
- `appointments(clinic_id, start)` — upcoming appointments / reminders.
- `messages(conversation_id, timestamp)` — conversation replay.
- `events(clinic_id, event_type, timestamp)` — funnel queries.
- Unique constraint on `(provider, external_id)` wherever webhook idempotency needs it (appointments, payments, messages) — this is the DB-level enforcement of CLAUDE.md §24's "never process the same webhook twice."

## What Phase 0 does NOT do

- No actual SQL migrations.
- No Supabase project created/connected.
- No pgvector table for embeddings (that's Phase 5, alongside the RAG pipeline).
- No seed data (Phase 2 deliverable, per CLAUDE.md §26/§35 demo clinic).
