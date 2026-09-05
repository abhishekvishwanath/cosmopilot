# Provider Interfaces — Phase 0

CLAUDE.md §5.6, §26 and §27 require every external service to sit behind an interface with a mock implementation, so core business logic never depends directly on a vendor SDK. This document defines the contract for each interface at a conceptual level. Actual Python code (`apps/api/app/providers/*`) is written in the phase that first needs it — not all upfront — per CLAUDE.md §31's phase plan:

| Interface | Mock implementation lands | Real implementation lands |
|---|---|---|
| `CalendarProvider` | Phase 7 | Later, once a clinic's real PMS/calendar is identified (CLAUDE.md §32 — never invented ahead of time) |
| `LLMProvider` | Phase 6 (or mock-only if no key yet) | Phase 5/6, once an AI provider key is supplied |
| `VoiceProvider` | Phase 6 (mock) | Phase 10 (Vapi) |
| `WhatsAppProvider` | Phase 6/8 (mock) | Phase 9 (Meta WhatsApp Cloud API) |
| `PaymentProvider` | Only if payments are needed | Phase 9+/on demand (Stripe test mode) |
| `EmailProvider` | Phase 4 (mock) | Whenever Resend key is supplied |

Every provider directory follows the same shape:

```text
app/providers/<capability>/
├── base.py     # abstract interface (Protocol or ABC)
├── mock.py     # deterministic, no-network implementation
└── <vendor>.py # real implementation, added when that phase starts
```

Core services depend on `base.py`'s interface type, constructed via a factory that reads config (`MOCK_MODE` / per-provider env flags) to decide which implementation to inject — so switching from mock to real is a config change, never a code change in `services/`.

## `LLMProvider`

Responsible for: conversational reasoning, tool-call selection, RAG-grounded answers.

```text
generate(messages, tools, clinic_context) -> LLMResponse
  - messages: conversation history (role, content)
  - tools: typed tool schemas available to the model (CLAUDE.md §12)
  - clinic_context: system-level clinic/treatment context injected by the caller
  - returns: assistant message and/or requested tool call(s), never a "final" business
    outcome by itself — tool calls still go through deterministic backend execution
    (CLAUDE.md §5.3)
```

Mock implementation returns scripted/templated responses sufficient to drive the demo flow (CLAUDE.md §26) without a real model call.

## `VoiceProvider`

Responsible for: placing/receiving an outbound AI phone call and relaying the conversation to the `LLMProvider` + tools.

```text
start_call(lead, clinic_context) -> CallHandle
  - initiates an outbound call to the lead's phone number

handle_call_event(payload) -> CallEvent
  - normalizes a provider webhook payload (e.g. Vapi) into a common event:
    answered | no_answer | ended | transcript_chunk | tool_call

get_call_summary(call_id) -> CallSummary
  - structured summary + outcome (booked / escalated / no_answer / lost),
    never free text alone deciding lead state (CLAUDE.md §9)
```

Mock implementation simulates a call outcome (e.g. deterministically alternating answered/no-answer, or configurable per demo scenario) without any real telephony.

## `WhatsAppProvider`

Responsible for: sending/receiving WhatsApp messages for the fallback flow and any WhatsApp-native concierge conversation.

```text
send_message(to, template_or_text, clinic_context) -> MessageHandle
receive_webhook(payload) -> IncomingMessage
  - normalizes Meta's webhook payload into a common inbound-message shape
verify_opt_out(lead) -> bool
  - checked before every outbound send (CLAUDE.md §16 — respect opt-outs, no spam)
```

Mock implementation logs the "sent" message to the conversation record instead of calling Meta's API, and can simulate an inbound reply for demo purposes.

## `CalendarProvider`

Responsible for: availability truth, booking, rescheduling, cancellation. This is the provider CLAUDE.md §18 is most explicit about — it is the source of truth, never the LLM.

```text
get_availability(clinic_id, doctor_id, treatment_id, date_range) -> list[Slot]
book(clinic_id, slot, lead) -> Appointment
reschedule(appointment_id, new_slot) -> Appointment
cancel(appointment_id, reason) -> Appointment
get_status(appointment_id) -> AppointmentStatus
```

`MockCalendarProvider` (Phase 7) is seeded with realistic slots per doctor/treatment and enforces the same booking constraints a real provider would (no double-booking, respects opening hours) so the demo behaves believably and the interface is exercised honestly.

## `PaymentProvider`

Responsible for: optional deposit/payment collection, only if a clinic requires it (CLAUDE.md §2 — out of scope by default).

```text
create_payment_link(clinic_id, appointment_id, amount, currency) -> PaymentLink
handle_webhook(payload) -> PaymentEvent
get_status(payment_id) -> PaymentStatus
```

No card data ever passes through or is stored by CosmoPilot (CLAUDE.md §23) — Stripe-hosted checkout/payment links only.

## `EmailProvider`

Responsible for: confirmations, reminders, staff notifications where email is the right channel.

```text
send(to, template, context) -> EmailHandle
```

Mock implementation logs the would-be email instead of calling Resend.

## Design rules that apply to every provider

- **Fail safely, never fabricate success** (CLAUDE.md §25) — a provider call that fails raises/returns a typed error; the caller (service layer) decides the graceful fallback (e.g. "create `HUMAN_REQUIRED` task"), the provider itself never pretends an action succeeded.
- **Structured output only** — every method returns a typed object, not a raw provider payload, so `services/` never depends on a vendor's response shape.
- **Clinic-scoped** — every call takes/validates a `clinic_id` so cross-clinic leakage is impossible even at the provider layer (defense in depth alongside RLS and API-layer checks).
- **Logged** — every provider call logs enough to reconstruct what was attempted, independent of whether it succeeded (CLAUDE.md §23 audit logs).

## What Phase 0 does NOT do

- No Python code for any of these interfaces yet — this document is the contract; implementation starts in the phase column above.
- No vendor SDKs installed yet.
