# Architecture — Phase 0

Source of truth for product/business rules is [CLAUDE.md](../CLAUDE.md). This document records the concrete architectural decisions made in Phase 0 and how the system fits together.

## 1. Monorepo layout

```text
cosmopilot/
├── apps/
│   ├── web/            # Next.js (App Router) — public site, forms, admin/CRM UI
│   └── api/             # FastAPI — business logic, AI orchestration, providers
├── workflows/
│   └── n8n/              # Exported n8n workflow JSON (Workflows A–G, see CLAUDE.md §17)
├── packages/
│   ├── types/            # Shared TypeScript types (API contracts, DB row shapes) consumed by apps/web
│   └── config/           # Shared lint/tsconfig/tailwind config consumed by apps/web
├── docs/                 # Architecture, database, API convention docs (this folder)
├── tests/                 # Cross-app / E2E (Playwright) tests
├── scripts/               # One-off dev/ops scripts (seeding, migration helpers)
├── docker/                # Dockerfiles + compose fragments
├── .env.example
├── docker-compose.yml     # Added in Phase 1
└── CLAUDE.md
```

Rationale: `apps/*` keeps the two runtimes (Node/Next.js, Python/FastAPI) independently deployable (Vercel for `web`, Railway for `api`) while `packages/types` gives the frontend a typed view of API/DB contracts without the backend depending on the frontend. This matches CLAUDE.md §29 exactly.

## 2. Runtime choices (Phase 0 defaults)

These are sensible defaults, not locked-in forever — they can be revisited if a real constraint shows up.

| Concern | Choice | Why |
|---|---|---|
| Node.js | 20 LTS | Current Next.js 14+ minimum, long support window |
| Package manager | npm workspaces | Built into Node, no extra global install, monorepo-capable via `apps/*`, `packages/*` workspaces |
| Python | 3.11+ | FastAPI/Pydantic v2 baseline, good async performance |
| Python env/deps | `venv` + `pip` + `pyproject.toml` (or `requirements.txt` if simpler) | No extra tooling required; revisit `uv`/`poetry` only if dependency management becomes painful |
| Frontend | Next.js (App Router) + TypeScript + Tailwind + shadcn/ui | Per CLAUDE.md §6 |
| Backend | FastAPI + Pydantic | Per CLAUDE.md §6 |
| DB | Supabase (Postgres + pgvector) | Per CLAUDE.md §6 |
| Local dev parity | Docker Compose (Phase 1) | Runs `api`, and optionally a local Postgres, consistently across machines |

## 3. High-level system architecture

See CLAUDE.md §7 for the full diagram. Summary of responsibility boundaries:

- **`apps/web` (Next.js)** — public marketing/landing pages, enquiry form, WhatsApp/AI concierge entry points, admin CRM dashboard UI. No business logic; calls the FastAPI API.
- **`apps/api` (FastAPI)** — all business logic: lead processing, AI orchestration + tool execution, appointment logic, provider adapters, webhook handling, auth checks. This is where CLAUDE.md §5.3 ("deterministic logic for critical actions") is enforced.
- **Supabase/Postgres** — system of record: clinics, leads, conversations, appointments, events, consents. `apps/api` is the only writer for state that matters (CRM, appointments); `apps/web` only reads via API-issued session/service calls, never talks to Postgres directly.
- **n8n** — orchestration only (delays, retries, fan-out to notifications). It calls into FastAPI webhooks/endpoints for anything that mutates core state; n8n itself holds no source-of-truth data. See CLAUDE.md §17 for the 7 workflows this will run (A–G).
- **Provider adapters** (`apps/api/app/providers/*`) — one interface per external capability (LLM, Voice, WhatsApp, Calendar, Payments, Email), each with a `mock` implementation and a real implementation added only in the phase that needs it (Vapi in Phase 10, Meta WhatsApp in Phase 9, etc.). See `docs/PROVIDER_INTERFACES.md`.

## 4. Backend internal structure (created in Phase 1, documented here for reference)

```text
apps/api/app/
├── api/            # FastAPI routers, one module per resource group (CLAUDE.md §28)
├── core/           # settings, security, logging, startup/shutdown
├── models/         # ORM/DB row models
├── schemas/        # Pydantic request/response schemas
├── services/       # business logic (lead service, appointment service, etc.)
├── providers/      # provider interfaces + mock/real adapters
├── agents/         # AI concierge: system prompts, tool definitions, orchestration
├── workflows/       # internal workflow helpers invoked by n8n webhooks
├── repositories/    # DB access layer, clinic-scoped queries
└── utils/
```

Business logic stays out of route handlers (`api/`) — routers validate input/auth and delegate to `services/`.

## 5. Environment separation

- **Demo/mock mode**: default. No production credentials required — every provider falls back to its `Mock*Provider`. Mocked integrations are visibly labeled in the UI (CLAUDE.md §26).
- **Real integrations**: enabled per-provider via env vars, introduced only in the phase that needs them (CLAUDE.md §32). Switching a provider from mock to real must not require touching core business logic — only the provider adapter + config.

## 6. What Phase 0 deliberately does NOT do

- No FastAPI/Next.js application code yet (Phase 1).
- No database migrations or Supabase project connection yet (Phase 1/2).
- No provider adapter *implementations* — only the interface contracts are defined (`docs/PROVIDER_INTERFACES.md`); code lands when each provider's phase starts.
- No Docker Compose file yet — `docker/` exists as a placeholder, actual Dockerfiles come in Phase 1.

## 7. Open architectural questions (non-blocking, default assumed)

None block Phase 0. If any of these should change, flag it before Phase 1 starts:

- Supabase project: assumed to be created fresh in Phase 1 unless the user has an existing project to point at.
- Hosting: assumed Vercel (web) + Railway (api) + n8n Cloud, per CLAUDE.md §6, deferred until a deploy is actually needed.
