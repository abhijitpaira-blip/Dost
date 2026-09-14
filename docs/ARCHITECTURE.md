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
  backend routes in Phase 1.

## What's deliberately NOT here yet

AI chat, voice/Speechma, memory, communication coach, learning engine, motivation/gamification, admin
dashboard, daily challenges — all of these are `services/<name>` stub packages with a docstring and
nothing else. Wiring one in later means: build the logic in its `services/` package, add a route in
`backend/app/api/v1/`, register it in `router.py`, and add a screen in `frontend/src/app/(app)/`.

## Deployment target (not yet deployed)

- Frontend → Vercel (`frontend/` as the project root)
- Backend → Railway (`backend/` as the project root; `services/` needs to ship alongside it — see
  `docs/PHASE1_REPORT.md` for the one config decision this requires)
- Database/Auth → Supabase
