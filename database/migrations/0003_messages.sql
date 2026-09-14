-- DOST Phase 3: chat memory — persists conversation turns so a page
-- reload (or a new device) doesn't lose what was said.
--
-- Context: backend/app/api/v1/chat.py previously had no persistence at
-- all — the frontend sent the whole message history on every request and
-- nothing was written to the database (see that file's old docstring,
-- which pointed here: "That's Phase 3 (services/memory)"). This adds the
-- table services/memory/store.py writes to and frontend/src/lib/chat/
-- reads from.
--
-- Run against the project's Supabase Postgres database (via Supabase SQL
-- editor, `supabase db push`, or the Supabase MCP `apply_migration` tool),
-- after 0001_init_profiles.sql and 0002_guardian_consent.sql.

create table if not exists public.messages (
  id            uuid primary key default gen_random_uuid(),
  auth_user_id  uuid not null references auth.users (id) on delete cascade,
  role          text not null check (role in ('user', 'assistant')),
  content       text not null,
  created_at    timestamptz not null default now()
);

comment on table public.messages is
  'One row per chat turn (user message or DOST reply). Written by
   services/memory/store.py after backend/app/api/v1/chat.py gets a
   reply back from the AI provider - never directly by the frontend.
   Read directly by the frontend (like profiles) to restore a
   conversation on page load - see frontend/src/lib/chat/useChatHistory.ts.';

-- Row Level Security: a user may only ever see their own messages. The
-- backend writes with the service-role key (bypasses RLS, same as
-- backend/app/core/supabase.py's client) - these policies exist for
-- direct frontend reads and as defense in depth, not because the backend
-- depends on them.
alter table public.messages enable row level security;

drop policy if exists "messages_select_own" on public.messages;
create policy "messages_select_own"
  on public.messages for select
  using (auth.uid() = auth_user_id);

drop policy if exists "messages_insert_own" on public.messages;
create policy "messages_insert_own"
  on public.messages for insert
  with check (auth.uid() = auth_user_id);

-- No update/delete policy on purpose, same reasoning as profiles: not
-- needed yet, and account/conversation deletion is future server-side
-- work, not a direct user action.

create index if not exists idx_messages_auth_user_id_created_at
  on public.messages (auth_user_id, created_at);
