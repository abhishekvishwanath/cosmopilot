# apps/api

CosmoPilot's FastAPI backend — business logic, AI orchestration, provider adapters, webhooks. Phase 1 ships the app shell, config/logging foundation, health checks, and Supabase Auth JWT verification.

Stack: Python 3.11+ · FastAPI · Pydantic v2 · pydantic-settings.

## Setup

```bash
cd apps/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env       # fill in Supabase values when you have them — runs fine without them (mock mode)
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/api/v1/health` and `/api/v1/health/ready`.

## Commands

| Command | Purpose |
|---|---|
| `uvicorn app.main:app --reload --port 8000` | Start the dev server |
| `pytest` | Run tests |
| `ruff check .` | Lint |
| `mypy app tests` | Type check |

Or from the repo root: `make lint`, `make typecheck`, `make test`, `make dev-api`.

## Environment variables

See [.env.example](.env.example). The app runs fully in mock mode with none of the Supabase variables set — `/health/ready` reports `"database": "not_configured"` (a valid, expected state) rather than failing. For how to get real Supabase values, see the root [README.md](../../README.md#supabase-setup-phase-1).

## Structure

```text
app/
├── main.py           # FastAPI app, CORS, structured request logging, error format
├── core/
│   ├── config.py       # pydantic-settings Settings, read from .env
│   ├── logging.py       # structured logging setup
│   └── security.py       # Supabase JWT verification (JWKS, HS256 fallback) + get_current_user
├── api/v1/
│   ├── router.py          # aggregates all v1 routers
│   ├── health.py            # /health (liveness), /health/ready (checks Supabase reachability)
│   └── auth.py                # /auth/me — proves JWT verification works end to end
├── db/
│   └── supabase.py             # lightweight Supabase reachability check (no SDK dependency yet)
├── models/ schemas/ services/ providers/ agents/ workflows/ repositories/ utils/
│   # empty — populated starting Phase 2, per docs/ARCHITECTURE.md
tests/
├── test_health.py
├── test_auth.py
├── test_db_supabase.py
└── test_security_jwks.py
```

## Notes

- Clinic-scoped authorization (matching a user to a `clinic_id`) is added in Phase 2 once the `clinics`/staff tables exist. `get_current_user` in Phase 1 only proves *who* the caller is via a valid Supabase JWT.
- JWT verification tries the project's JWKS endpoint first (`SUPABASE_URL` alone is enough — this is what current Supabase projects with asymmetric "JWT Signing Keys" require), falling back to `SUPABASE_JWT_SECRET` (HS256) only if no JWKS key matches, for older projects still on the legacy shared secret. Verified end-to-end against a real Supabase-issued token during Phase 1.
- The `/health/ready` Supabase check hits PostgREST's root endpoint directly over HTTP rather than pulling in the full `supabase-py` SDK, since no application table exists yet — this keeps Phase 1's dependency footprint minimal. It prefers `SUPABASE_SERVICE_ROLE_KEY` when set, since PostgREST restricts this introspection endpoint to `service_role` and would otherwise report a false error for anon-key-only setups.
