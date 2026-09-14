# Database

Supabase Postgres. Migrations are the source of truth for schema — don't hand-edit
the schema in the Supabase dashboard without adding a matching migration file here.

## Applying migrations

Pick one:

1. **Supabase SQL editor** — paste the contents of `migrations/0001_init_profiles.sql` and run.
2. **Supabase CLI** — `supabase link --project-ref <ref>` then `supabase db push`.
3. **Supabase MCP tool** (if you're driving this from Claude with the Supabase connector
   connected) — ask Claude to apply the migration to a named project. Claude will show
   you the project and ask before running anything that costs money or touches prod.

## What 0001 sets up

- `public.profiles` — one row per user, keyed by `auth_user_id` (the Supabase Auth UUID).
  `name` + `age` are just profile fields, never an identifier.
- A trigger that creates a blank profile row automatically the moment someone signs up.
- Row Level Security, on by default: a user can only `select`/`update`/`insert` their
  *own* row (`auth.uid() = auth_user_id`). No client-side delete policy — account
  deletion goes through a server-side (service-role) flow in a later phase, so it can
  also clean up chat history, memory, etc. in one transaction.

## No live project connected yet

Phase 1 did not create or modify a live Supabase project — see `docs/PHASE1_REPORT.md`
for why, and what's needed from you to connect one.
