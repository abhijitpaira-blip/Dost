-- DOST Phase 1: profiles foundation
-- Run this against the project's Supabase Postgres database
-- (via Supabase SQL editor, `supabase db push`, or the Supabase MCP `apply_migration` tool).

create extension if not exists "pgcrypto";

create table if not exists public.profiles (
  id             uuid primary key default gen_random_uuid(),
  auth_user_id   uuid not null unique references auth.users (id) on delete cascade,
  name           text,
  age            integer,
  preferred_language text default 'en',
  avatar         text,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now()
);

comment on table public.profiles is
  'One row per DOST user. Identity is auth_user_id (Supabase Auth UUID) — never name+age.';

-- Keep updated_at fresh on every change
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists trg_profiles_updated_at on public.profiles;
create trigger trg_profiles_updated_at
  before update on public.profiles
  for each row
  execute function public.set_updated_at();

-- Auto-create a profile row the moment a user signs up in Supabase Auth
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (auth_user_id)
  values (new.id)
  on conflict (auth_user_id) do nothing;
  return new;
end;
$$;

drop trigger if exists trg_on_auth_user_created on auth.users;
create trigger trg_on_auth_user_created
  after insert on auth.users
  for each row
  execute function public.handle_new_user();

-- Row Level Security: a user may only ever see/edit their own profile
alter table public.profiles enable row level security;

drop policy if exists "profiles_select_own" on public.profiles;
create policy "profiles_select_own"
  on public.profiles for select
  using (auth.uid() = auth_user_id);

drop policy if exists "profiles_update_own" on public.profiles;
create policy "profiles_update_own"
  on public.profiles for update
  using (auth.uid() = auth_user_id)
  with check (auth.uid() = auth_user_id);

drop policy if exists "profiles_insert_own" on public.profiles;
create policy "profiles_insert_own"
  on public.profiles for insert
  with check (auth.uid() = auth_user_id);

-- No delete policy is defined on purpose: account deletion is handled server-side
-- (service role, via the future `services/auth` account-deletion flow), not directly by users.

create index if not exists idx_profiles_auth_user_id on public.profiles (auth_user_id);
