# workflows/n8n

n8n workflow JSON for Phase 8 (CLAUDE.md §17). Built and validated with the
`n8n-mcp` MCP server's `validate_workflow`/`validate_node` tools — all four
files below validate with zero errors and zero warnings.

Workflows C (appointment booked) and F (no-show recovery) from CLAUDE.md
§17's full spec are combined into one n8n workflow
(`workflow-appointment-status-changed.json`): FastAPI dispatches a single
generic `appointment.status_changed` event for every status transition
(the one choke point in `services/appointments.py::transition_appointment_status`),
and a real n8n instance can only register one workflow per webhook path —
so this workflow branches internally on `to_status` instead of two
workflows racing for the same path.

| File | CLAUDE.md §17 | Trigger | Live on n8n Cloud |
|---|---|---|---|
| `workflow-a-new-lead.json` | Workflow A | Webhook `lead.created` | [Active](https://abhi-vishwa009.app.n8n.cloud/workflow/ALsVsSQykCqWHVPJ) |
| `workflow-b-call-unanswered.json` | Workflow B | Webhook `call.unanswered` (called by Workflow A) | [Active](https://abhi-vishwa009.app.n8n.cloud/workflow/VqHm6PKXInJyXaZe) |
| `workflow-appointment-status-changed.json` | Workflows D + F | Webhook `appointment.status_changed` | [Active](https://abhi-vishwa009.app.n8n.cloud/workflow/LF2qrB20T42hutcu) |
| `workflow-appointment-reminders.json` | Workflow E | Schedule (every 15 min — demo cadence) | [Active](https://abhi-vishwa009.app.n8n.cloud/workflow/moFF6w5cO5GZjhA7) |

All four were built and deployed directly on `abhi-vishwa009.app.n8n.cloud` via the `n8n-cloud` MCP server (translated from this JSON into the n8n Workflow SDK — the JSON files here remain the source of truth for the node graph and are kept in sync manually) and are **active**. What's still required before they actually work end-to-end:

1. **Set the n8n Variables** below (Settings → Variables on the n8n Cloud instance) — the workflows are live but every HTTP Request node will fail until these exist.
2. **Make FastAPI publicly reachable** — the deployed workflows call `COSMOPILOT_API_URL`, which can't be `localhost` from n8n Cloud. Point a tunnel (e.g. `ngrok http 8000`) or a real deployment at it and set the variable accordingly.

Workflow G (payment) is out of scope — CLAUDE.md §2/§32 don't require
payment functionality for this prototype. Workflow C (WhatsApp incoming)
needs a live Meta WhatsApp webhook and lands in Phase 9.

## Importing

In n8n: **Workflows → Import from File**, pick each JSON, then:

1. Add the required Variables (**Settings → Variables**, n8n Cloud) —
   every workflow references these instead of hardcoding values:
   - `COSMOPILOT_API_URL` — the FastAPI deployment's public base URL plus
     `/api/v1`, e.g. `https://your-api-host.example.com/api/v1` (local dev:
     an n8n Cloud instance can't reach `localhost`, so local testing needs
     a tunnel — e.g. `ngrok http 8000` — pointed at the FastAPI dev server).
   - `COSMOPILOT_WEBHOOK_SECRET` — must match `N8N_WEBHOOK_SHARED_SECRET`
     in `apps/api/.env` exactly.
   - `N8N_INSTANCE_URL` — this n8n instance's own base URL (e.g.
     `https://your-instance.app.n8n.cloud`), only needed by Workflow A to
     call Workflow B.
   - `CLINIC_ID` — the demo clinic's UUID, only needed by the Reminders
     workflow's Schedule Trigger (the other workflows get `clinic_id` from
     the incoming webhook payload).
2. **Activate** each workflow (top-right toggle) — inactive workflows
   don't register their webhook path.
3. Set `N8N_WEBHOOK_BASE_URL` in `apps/api/.env` to this n8n instance's
   base URL (e.g. `https://your-instance.app.n8n.cloud`) and
   `N8N_WEBHOOK_SHARED_SECRET` to the same value as `COSMOPILOT_WEBHOOK_SECRET`
   above — FastAPI builds outbound URLs as `{N8N_WEBHOOK_BASE_URL}/webhook/{event}`
   (see `app/services/n8n.py`).

## What FastAPI expects back

Every `HTTP Request` node in these workflows calls
`/api/v1/webhooks/n8n/*` (see `app/api/v1/webhooks.py`), authenticated by
the `X-Webhook-Secret` header. Every state-changing action there is
idempotent (re-running the same step twice never double-contacts a
patient or double-transitions a status) — see that file's module
docstring for the CLAUDE.md §24 reasoning.
