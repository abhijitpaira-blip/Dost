# Architecture — Phase 1

## Design plan (visual foundation)

- **Color:** `linen-50 #FBFAF6` / `linen-100 #F4F1E8` (warm neutral base) · `ink-900 #141B19` (near-black
  text, not pure black) · `amber-500 #D8912A` (primary warm accent — for focus states, actions) ·
  `clay-500 #B6644C` (secondary accent — used sparingly, e.g. links, the "DOST" wordmark). Deliberately
  not the `#D97757` terracotta-on-cream combination that's become a generic AI-app tell.
- **Type:** Fraunces (serif, italic-leaning) for the headline moments — warm and a little literary, fits
  "a friend," not a clinical tool. Inter for everything functional (body copy, forms, nav).
- **Layout:** single-column, left-aligned, mobile-first (max-w-md/lg), generous vertical rhythm. No
  cards-with-shadows kit, no numbered-step chrome — there's no sequence to number yet in Phase 1.
- **Principle:** restraint. Phase 1 is a shell, not a marketing site — it should feel calm and unfinished
  in the right way, not padded out with placeholder sections.

## Why a top-level `services/` package

The backend (`backend/app`) is kept as a thin FastAPI layer: routing, request/response models, auth
dependency wiring. Actual behavior lives in `services/<capability>`, imported by the backend. This
mirrors the spec's explicit ask for `services/ai`, `services/voice`, etc. as separate modules, and means
a future service (say, `services/voice`) can be developed, tested, and reasoned about without touching
`backend/app` at all.

## Auth model

- Identity is **`auth_user_id` (Supabase Auth UUID)** — never name+age, never email as a key.
- Supabase Auth handles email/password now; mobile OTP, Google, and Apple sign-in are configured in the
  Supabase dashboard later (Phase 1 code doesn't block any of them — `supabase.auth.signInWithOAuth` /
  `signInWithOtp` are drop-in additions to the same `lib/supabase/client.ts`).
- Every signup fires a Postgres trigger that creates a blank `profiles` row — the app never has to
  remember to do this itself.
- The backend's `services/auth/verify.py` establishes the shape for protected routes (verify the
  Supabase JWT → get `auth_user_id`) but isn't attached to any route yet, since there are no protected
  backend routes in Phase 1. Phase 3 adds `get_current_user_id_optional`, a non-raising variant used by
  `/chat` so an unauthenticated caller still gets a reply — it just isn't remembered.

## What's here now vs. still deliberately not

AI chat, voice/Speechma, chat memory (the raw transcript only — see below), a deterministic safety
net (see below), Communication Coach (see below), and an admin dashboard (see below) are built. Learning
engine and motivation/gamification beyond the daily streak (e.g. daily challenges) are still
`services/<name>` stub packages with a docstring and nothing else. Wiring one in later means: build the
logic in its `services/` package, add a route in `backend/app/api/v1/`, register it in `router.py`, and
add a screen in `frontend/src/app/(app)/`.

`services/safety` is the one exception to "still a stub": `core.md`'s Section 9 already instructs the AI
to respond to serious distress with care and point toward real support, but prompt-following can be
imperfect, so `chat.py` also runs the user's latest message through `detect_crisis_signal()` — a narrow,
regex-based keyword net over explicit self-harm/suicide phrasing (English fairly thoroughly; Hindi/Bengali
limited to the single verified word for "suicide" plus common Hinglish spellings — indirect or slang
phrasing in any language is a known, real gap, not a guarantee). When it fires and the AI's own reply
didn't already mention a helpline, a footer with verified government helpline numbers (Tele MANAS, KIRAN,
and 112) is appended — never a replacement for the AI's own response, only a deterministic backstop under
it. See `services/safety/__init__.py`'s docstring for the full scope and honest limitations.

Chat memory (`services/memory/store.py`) is deliberately narrow: it persists the raw transcript
(`public.messages`, `database/migrations/0003_messages.sql`) so a reload doesn't lose the conversation
and it's identical to what the frontend already sends the AI provider — it does **not** yet distill or
summarize anything (no "remembers you like hiking," no cross-session facts). That's still future work.

The Home screen (`frontend/src/app/(app)/dashboard/page.tsx`) greets the user by name and shows a
genuine activity summary — how many messages they've exchanged, when they last talked, and (as of the
daily streak below) a real streak count — read directly from `public.messages` the same way
`useChatHistory.ts` does — plus a CTA into `/chat`. It is not a dashboard for every feature yet; anything
still a stub (learning, admin, daily challenges) lands on this same screen via `BottomNav`'s placeholder
links until it exists for real.

The daily streak (`frontend/src/lib/chat/streak.ts`) is the first genuinely persisted piece of core.md's
Section 10 (gamification) — until now the AI could only ever *talk about* streaks in a reply, nothing was
tracked. It's a pure function over the distinct calendar days (from the last 90 days of the user's own
messages) that have at least one message, computed server-side in `dashboard/page.tsx` off the *server's*
clock rather than the user's own timezone — an acceptable tradeoff for a motivational number, not
something to build precise logic (reminders, notifications) on top of without revisiting that. No
leaderboard, no penalty for a missed day, per core.md's existing gamification rule.

Communication Coach (`services/ai/prompts/communication_coach.md`, `frontend/src/app/(app)/coach/page.tsx`)
is a practice-conversation mode, not a separate backend feature: the frontend's `/coach` screen sends the
same `/api/v1/chat` request shape as normal chat, plus a `scenario` string describing what the user wants
to practice (e.g. "asking my manager for a raise"). When `scenario` is present, `build_system_prompt`
appends `communication_coach.md` and a block naming that scenario, on top of — never instead of — `core.md`
and the user's age-band block, so the always-on identity/safety/scope rules and the safety net above keep
applying unchanged during roleplay. DOST plays a realistic counterpart character (calibrated to the traits
the user describes, redirecting a request to play a *named real public figure* to a generic version of that
role instead), then switches to concrete feedback when asked. Coach turns are deliberately **not** saved to
`public.messages` — mixing a practiced argument with a "strict boss" character into the same transcript the
Home screen, streak, and `/chat` history all read from would be confusing — so a practice session lives only
in the browser tab; a dedicated coach-history table is possible future work, not built now.

The admin dashboard (`services/admin/stats.py`, `backend/app/api/v1/admin.py`,
`frontend/src/app/(app)/admin/page.tsx`) is a handful of aggregate usage counts for the app owner — total
users, total messages, messages today, distinct users active in the last 7 days, new signups in the last 7
days — not a general analytics/BI tool. It reads with the service-role Supabase client (the same one
`services/memory/store.py` uses) because these are cross-user counts that profiles' and messages' RLS
policies (scoped to "a user may only ever see their own row") should never need to allow directly from the
frontend. Gating who can call it is a new dependency, `services.auth.get_current_admin_user_id`: same JWT
verification as every other protected route, plus a check that the caller's `auth_user_id` (never an email —
see this doc's Auth model) is in the `ADMIN_USER_IDS` env var. That's an env var the owner sets, not a
database column/flag — for a single-owner app it needs no migration or extra RLS policy; see
`backend/.env.example` for how to find your own Supabase Auth UUID. `/admin` has no link anywhere in the
app's nav on purpose (it's not in `BottomNav`) — it's opened directly by whoever's allow-listed, not a
feature meant for the rest of the family to stumble into.

## Deployment target (not yet deployed)

- Frontend → Vercel (`frontend/` as the project root)
- Backend → Railway (`backend/` as the project root; `services/` needs to ship alongside it — see
  `docs/PHASE1_REPORT.md` for the one config decision this requires)
- Database/Auth → Supabase
