# CosmoPilot

AI Patient Acquisition & Appointment Automation for premium cosmetic clinics.

CosmoPilot turns AI/search discovery into booked consultations: a visitor lands on a treatment page, submits an enquiry, and is contacted by an AI Patient Concierge within roughly 60 seconds — by phone call, with a WhatsApp fallback if unanswered — that qualifies them and books an appointment, all tracked in a CRM the clinic staff can see in real time.

Full product spec, architecture, and phase plan: **[CLAUDE.md](CLAUDE.md)**.

## Status

**Phase 1 — Foundation.** Next.js and FastAPI app shells, Docker, structured logging, health checks, and Supabase Auth JWT verification are wired up. The full stack runs in mock mode without any credentials — see [Setup](#setup) to run it locally.

See [docs/](docs/) for the Phase 0 architecture/planning deliverables:

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — system architecture, monorepo layout, runtime choices
- [docs/DATABASE.md](docs/DATABASE.md) — data model plan
- [docs/API_CONVENTIONS.md](docs/API_CONVENTIONS.md) — REST API conventions
- [docs/PROVIDER_INTERFACES.md](docs/PROVIDER_INTERFACES.md) — external provider abstraction contracts

## Project structure

```text
cosmopilot/
├── apps/
│   ├── web/          # Next.js — public site, forms, CRM/admin UI
│   └── api/           # FastAPI — business logic, AI orchestration, providers
├── workflows/
│   └── n8n/            # n8n workflow exports (Phase 8+)
├── packages/
│   ├── types/           # Shared TypeScript types (Phase 2+)
│   └── config/           # Shared lint/tsconfig/tailwind config (Phase 3+)
├── docs/                 # Architecture & planning docs
├── tests/                 # Cross-app / E2E tests (Playwright, Phase 3+)
├── scripts/               # Dev/ops scripts
├── docker/                # Dockerfiles (api.Dockerfile, web.Dockerfile)
├── docker-compose.yml
├── Makefile               # make dev-web / dev-api / lint / typecheck / test / build
├── package.json           # npm workspace root (apps/web)
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

Requires Node.js 20+ and Python 3.11+.

```bash
# 1. Frontend
cd apps/web
npm install
cp .env.example .env.local
npm run dev                 # http://localhost:3000

# 2. Backend (separate terminal)
cd apps/api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000   # http://localhost:8000
```

Or from the repo root: `make install`, then `make dev-web` / `make dev-api` in separate terminals. `make lint`, `make typecheck`, `make test`, `make build` run both apps' checks together.

Visit `http://localhost:3000/health` — it calls the FastAPI backend live and shows liveness + readiness status. Everything works with **no credentials at all**: `/health/ready` reports the database as `"not_configured"` (expected in mock mode) rather than failing.

Never commit real secrets — `.env` / `.env.local` are gitignored. See [CLAUDE.md §23](CLAUDE.md#23-security--privacy).

### Docker

```bash
docker compose up --build
```

Builds both apps from `docker/api.Dockerfile` and `docker/web.Dockerfile`, reading `apps/api/.env` and `apps/web/.env.local` (create these first, per above).

### Supabase setup (Phase 1)

Phase 1 wires up Supabase Auth verification and a live database readiness check, but **nothing breaks without it** — skip this section to keep developing in mock mode, and come back when you're ready to connect a real project (needed properly starting Phase 2, for the CRM database).

**Why:** Supabase is CosmoPilot's database (Postgres + pgvector) and auth provider (CLAUDE.md §6). **Cost:** the Free tier is enough for the whole prototype — no credit card required.

1. **Create an account.** Go to [supabase.com](https://supabase.com) → **Start your project** → sign up (GitHub sign-in is fastest).
2. **Create a new project.**
   - Click **New Project** (create an organization first if this is your first project — any name is fine, e.g. "CosmoPilot").
   - **Name:** `cosmopilot-dev` (or similar).
   - **Database Password:** click "Generate a password" and **save it somewhere safe** (a password manager) — you'll need it later for `DATABASE_URL`. It is *not* the same as any of the API keys below.
   - **Region:** pick whichever is closest to you/your users (there's no UAE region yet — Mumbai (`ap-south-1`) is usually the lowest-latency choice for Dubai).
   - **Plan:** Free.
   - Click **Create new project** and wait 1–2 minutes while it provisions.
3. **Get the API credentials.** Once the project is ready, go to **Project Settings** (the gear icon, bottom of the left sidebar) → **API** (in some dashboard versions this is labeled **Data API**).
   - **Project URL** — looks like `https://xxxxxxxxxxxx.supabase.co`. This is `SUPABASE_URL` / `NEXT_PUBLIC_SUPABASE_URL`.
   - **Project API keys → `anon` `public`** — safe to expose in the browser (Row-Level Security protects the data). This is `SUPABASE_ANON_KEY` / `NEXT_PUBLIC_SUPABASE_ANON_KEY`.
   - **Project API keys → `service_role` `secret`** — full-access key. **Never** put this in `apps/web`; it only ever goes in `apps/api/.env` as `SUPABASE_SERVICE_ROLE_KEY`.
4. **Get the JWT secret** (same **Project Settings → API** page, further down under **JWT Settings** — look for **JWT Secret**, sometimes labeled **Legacy JWT Secret**). Copy it into `apps/api/.env` as `SUPABASE_JWT_SECRET`. This is what `apps/api` uses to verify that a request really came from a logged-in Supabase user (CLAUDE.md §23).
   > If your project only shows newer asymmetric "JWT Signing Keys" and no HS256 secret is visible, tell me — the backend can be switched to verify via Supabase's JWKS endpoint instead, no app-code changes needed elsewhere.
5. **Get the database connection string** (for later phases' migrations): **Project Settings → Database → Connection string → URI**. Copy it into `apps/api/.env` as `DATABASE_URL`, replacing `[YOUR-PASSWORD]` with the password from step 2.
6. **Place the values:**
   - `apps/api/.env`: `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`, `DATABASE_URL`.
   - `apps/web/.env.local`: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` (anon key only — never the service role key here).
7. **Verify it worked:** restart `uvicorn`, then `curl http://localhost:8000/api/v1/health/ready` — `checks.database.status` should read `"ok"` instead of `"not_configured"`.

You don't need to paste these values into chat — just drop them into the `.env` files above; I can verify the connection by running the health check against your local `.env`, which doesn't print the secret values.

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
