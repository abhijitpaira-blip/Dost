# PHASE 2 COMPLETED — AI Chat Foundation

## What was built

**`services/ai/`** — provider-agnostic chat layer:
- `base.py` — `AIProvider` interface + `ChatMessage` type. Everything else in the codebase
  depends on this shape, never on a specific SDK.
- `anthropic_provider.py`, `openai_provider.py` — one implementation each, same interface.
- `provider.py` — `get_provider()` picks the active one from `AI_PROVIDER` env var
  (`anthropic` | `openai`, defaults to `anthropic`).
- `personality.py` — `DOST_SYSTEM_PROMPT`, DOST's voice (warm, listens first, short replies,
  gentle nudges, defers to real support if someone seems distressed).

**Backend** — `POST /api/v1/chat`: takes the full message history from the frontend, calls
`get_provider().send_message(...)`, returns `{ reply: string }`. AI provider errors surface as
a clean `502`, not a stack trace. No persistence — this phase doesn't save chat history
anywhere (that's `services/memory`, a later phase).

**Frontend** — new `/chat` screen (`frontend/src/app/(app)/chat/page.tsx`): a message list +
input, calls the backend endpoint, shows "DOST is thinking…" while waiting, shows a plain
error if the backend is unreachable. Bottom nav's "Talk" tab now links here (previously a
placeholder pointing at `/dashboard`).

**Tests** — `tests/backend/test_chat.py`: exercises the endpoint with a fake provider (no real
API key needed to run tests), checks the empty-messages 400 case.

## Environment variables added

```
AI_PROVIDER=anthropic          # anthropic | openai
ANTHROPIC_API_KEY=<your key>   # required when AI_PROVIDER=anthropic
# OPENAI_API_KEY=              # required when AI_PROVIDER=openai
```
All in `backend/.env` — never in a `NEXT_PUBLIC_*` frontend variable. The frontend never talks
to Anthropic/OpenAI directly; it only ever calls your own backend.

## What's deliberately NOT in this phase

- No chat history persistence — refreshing the page loses the conversation. That's the
  `services/memory` phase.
- No streaming responses — the frontend waits for the full reply. Can add later if wanted.
- No rate limiting or per-user usage tracking on `/api/v1/chat` — fine for local testing,
  worth adding before this is public.
- The chat endpoint isn't behind auth yet (`services/auth/verify.py` exists but isn't attached
  here) — anyone who can reach the backend can call it. Add `Depends(get_current_user_id)`
  to the route once you're ready to require login for chat.

## Verified

- All backend `.py` files compile clean (`python -m py_compile`).
- All frontend `.tsx`/`.ts` files pass a bracket-balance sanity check.
- Could not run `npm install` / `pip install` / `pytest` in this sandbox (no network) — same
  limitation as Phase 1. Run locally with the commands below.

## Commands to run locally

```bash
# Backend — pick up the new anthropic/openai packages
cd backend
pip install -r requirements.txt
# add ANTHROPIC_API_KEY=... to backend/.env
PYTHONPATH=.:.. uvicorn app.main:app --reload

# Tests
cd backend && pytest ../tests/backend -v

# Frontend — no new packages needed
cd frontend
npm run dev
```
Then sign in at `http://localhost:3000`, tap **Talk** in the bottom nav, and send a message.
