# CosmoPilot

AI Patient Acquisition & Appointment Automation for premium cosmetic clinics.

CosmoPilot turns AI/search discovery into booked consultations: a visitor lands on a treatment page, submits an enquiry, and is contacted by an AI Patient Concierge within roughly 60 seconds — by phone call, with a WhatsApp fallback if unanswered — that qualifies them and books an appointment, all tracked in a CRM the clinic staff can see in real time.

Full product spec, architecture, and phase plan: **[CLAUDE.md](CLAUDE.md)**.

## Status

**Phase 0 — Discovery & Architecture.** Project structure and planning docs only. No application code yet.

See [docs/](docs/) for the Phase 0 deliverables:

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — system architecture, monorepo layout, runtime choices
- [docs/DATABASE.md](docs/DATABASE.md) — data model plan
- [docs/API_CONVENTIONS.md](docs/API_CONVENTIONS.md) — REST API conventions
- [docs/PROVIDER_INTERFACES.md](docs/PROVIDER_INTERFACES.md) — external provider abstraction contracts

## Project structure

```text
cosmopilot/
├── apps/
│   ├── web/          # Next.js — public site, forms, CRM/admin UI (Phase 1+)
│   └── api/           # FastAPI — business logic, AI orchestration, providers (Phase 1+)
├── workflows/
│   └── n8n/            # n8n workflow exports (Phase 8+)
├── packages/
│   ├── types/           # Shared TypeScript types
│   └── config/           # Shared lint/tsconfig/tailwind config
├── docs/                 # Architecture & planning docs
├── tests/                 # Cross-app / E2E tests (Playwright)
├── scripts/               # Dev/ops scripts
├── docker/                # Dockerfiles + compose fragments
├── .env.example
└── CLAUDE.md              # Product & engineering source of truth
```

## Tech stack

- **Frontend:** Next.js, React, TypeScript, Tailwind CSS, shadcn/ui
- **Backend:** Python, FastAPI, Pydantic
- **Database:** Supabase (PostgreSQL + pgvector)
- **Automation:** n8n
- **Voice:** Vapi
- **WhatsApp:** Meta WhatsApp Cloud API
- **Email:** Resend
- **Payments:** Stripe (test mode, only if needed)

Every external provider sits behind an interface with a mock implementation, so the full demo runs end-to-end without any production credentials (see [docs/PROVIDER_INTERFACES.md](docs/PROVIDER_INTERFACES.md)).

## Setup

Setup instructions are added as each phase lands real code:

- **Phase 1** will add: Next.js + FastAPI local dev instructions, Docker Compose, and the first required credential (Supabase — project URL + anon key).
- Until then, this repo contains structure and documentation only.

Environment variables: copy [.env.example](.env.example) to `.env` when Phase 1 introduces the apps. Never commit real secrets — see [CLAUDE.md §23](CLAUDE.md#23-security--privacy).

## Build plan

CosmoPilot is built strictly phase-by-phase (CLAUDE.md §31), with a stop-and-review checkpoint after every phase. Each phase's app code stays in a working, demoable state before the next phase starts.

| Phase | Focus |
|---|---|
| 0 | Discovery & architecture *(current)* |
| 1 | Foundation (Next.js, FastAPI, Supabase, Docker, auth foundation) |
| 2 | Database + CRM |
| 3 | Premium website |
| 4 | Lead capture |
| 5 | AI knowledge base (RAG) |
| 6 | AI Patient Concierge |
| 7 | Appointment engine |
| 8 | n8n automation |
| 9 | Meta WhatsApp |
| 10 | Vapi (AI calling) |
| 11 | Analytics |
| 12 | Production hardening |
| 13 | Full demo E2E |
