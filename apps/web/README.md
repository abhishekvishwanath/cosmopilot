# apps/web

CosmoPilot's Next.js frontend — public site, enquiry form, AI concierge UI, and admin/CRM dashboard (later phases). Phase 1 ships only the app shell, Supabase client wiring, and a `/health` page that proves the frontend can reach `apps/api`.

Stack: Next.js 16 (App Router) · React 19 · TypeScript · Tailwind CSS · ESLint.

## Setup

```bash
cd apps/web
npm install
cp .env.example .env.local   # fill in NEXT_PUBLIC_API_URL and Supabase values
npm run dev                  # http://localhost:3000
```

Visit `/health` to confirm the frontend can reach the FastAPI backend (`apps/api` must be running — see [../api/README.md](../api/README.md)).

## Commands

| Command | Purpose |
|---|---|
| `npm run dev` | Start the dev server |
| `npm run build` | Production build |
| `npm start` | Run the production build |
| `npm run lint` | ESLint |
| `npm run typecheck` | `tsc --noEmit` |
| `npm test` | Placeholder — the E2E suite (Playwright) lands in `tests/` starting Phase 3 |

## Environment variables

See [.env.example](.env.example). Only `NEXT_PUBLIC_*` variables are readable in the browser (everything else stays server-side) — see [docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md). For how to get real Supabase values, see the root [README.md](../../README.md#supabase-setup-phase-1).

## Structure

```text
src/
├── app/            # App Router routes (page.tsx, layout.tsx, health/)
└── lib/
    └── supabase/    # Browser + server Supabase client factories (@supabase/ssr)
```

## Notes

- `AGENTS.md` / `CLAUDE.md` in this directory are auto-managed by the Next.js CLI (`next dev`/`next build` regenerate them) and point Claude/other coding agents at this Next.js version's local docs (`node_modules/next/dist/docs/`) since APIs can differ from training data. They're unrelated to the root [CLAUDE.md](../../CLAUDE.md), which is CosmoPilot's product spec — leave both as-is.
