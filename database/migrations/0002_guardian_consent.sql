-- DOST: onboarding completion + guardian consent for minor users.
--
-- Context: services/ai/prompts/onboarding_and_consent.md §1 flags that a
-- child should not self-serve through name/age/language entry with no
-- guardian involved, given India's DPDP Act (a "child" there is anyone
-- under 18, and processing a child's personal data requires verifiable
-- parental/guardian consent). This migration adds the columns the
-- onboarding flow (frontend/src/app/onboarding/) needs to enforce that.
--
-- IMPORTANT SCOPE NOTE: guardian_consent_given is SELF-ATTESTED (a
-- checkbox the person filling out onboarding ticks), not identity-verified
-- consent (no email confirmation link, no ID check). Treat this as a
-- first compliance step, not a complete one — see the onboarding page's
-- own comments for the same note.
--
-- Run against the project's Supabase Postgres database (via Supabase SQL
-- editor, `supabase db push`, or the Supabase MCP `apply_migration` tool),
-- after 0001_init_profiles.sql.

alter table public.profiles
  add column if not exists guardian_name text,
  add column if not exists guardian_email text,
  add column if not exists guardian_consent_given boolean not null default false,
  add column if not exists guardian_consented_at timestamptz,
  add column if not exists onboarding_completed_at timestamptz;

comment on column public.profiles.guardian_consent_given is
  'Self-attested consent captured in /onboarding for users under 18 — NOT identity-verified (no email confirmation or ID check). See database/migrations/0002_guardian_consent.sql.';

comment on column public.profiles.onboarding_completed_at is
  'Set once the /onboarding flow finishes (name + age + language, plus guardian consent when age < 18). frontend/src/app/(app)/layout.tsx redirects here until this is set. Also drives PromptUser.onboarding_complete — see services/ai/prompt_loader.py.';

-- No new RLS policies needed: profiles_update_own (0001_init_profiles.sql)
-- already covers every column on a user's own row, these included.
