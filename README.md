# DOST

**A Friend Who Listens, Understands & Helps You Grow.**

DOST is an AI personal companion app. This repository is being built in phases.
This is **Phase 1 — Project Foundation** only: folder structure, auth/database
scaffolding, and a bare app shell. No AI chat, voice, memory, coaching, or
gamification features exist yet — those come in later phases.

## Layout

```
dost/
├── frontend/     Next.js 14 (App Router) + TypeScript + Tailwind — mobile-first UI shell
├── backend/      FastAPI service — thin API layer, imports from services/
├── services/     Modular business logic, one package per capability
│   ├── ai/               (stub — Phase 2+)
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
