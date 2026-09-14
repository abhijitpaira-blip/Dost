# DOST

**A Friend Who Listens, Understands & Helps You Grow.**

DOST is an AI personal companion app. This repository is being built in phases.

- **Phase 1 — Project Foundation:** folder structure, auth/database scaffolding, app shell.
- **Supabase foundation:** live Supabase project, `profiles` table + RLS, auth wired end-to-end.
- **Phase 2 — AI Chat Foundation:** a working chat screen backed by a modular AI provider
  layer (Anthropic or OpenAI, switchable via `AI_PROVIDER`). No memory/history persistence
  yet, no voice, no communication coach, no gamification — those are later phases.

## Layout

```
dost/
├── frontend/     Next.js 14 (App Router) + TypeScript + Tailwind — mobile-first UI shell
├── backend/      FastAPI service — thin API layer, imports from services/
├── services/     Modular business logic, one package per capability
│   ├── ai/                (Phase 2 — modular Anthropic/OpenAI chat provider)
│   ├── voice/             (stub — Speechma integration, later phase)
│   ├── memory/            (stub — later phase)
│   ├── communication/     (stub — communication coach, later phase)
│   ├── learning/          (stub — later phase)
│   ├── motivation/        (stub — later phase)
│   ├── safety/            (stub — later phase)
│   └── auth/               (Phase 1 — Supabase auth helpers)
├── database/     SQL migrations for Supabase Postgres (source of truth for schema)
├── tests/        Backend + frontend tests
└── docs/         Architecture notes, env variable reference, phase reports
```

## Stack (target)

- **Frontend:** Next.js / React, TypeScript, Tailwind, mobile-first — deploys to Vercel
- **Backend:** FastAPI (Python) — deploys to Railway
- **Database/Auth:** Supabase (Postgres + Supabase Auth, Row Level Security everywhere)
- **AI:** modular provider layer (not implemented yet)
- **Voice:** Speechma TTS (not implemented yet)

See `docs/ARCHITECTURE.md` for the full picture and `docs/PHASE1_REPORT.md` for
exactly what Phase 1 delivered.
