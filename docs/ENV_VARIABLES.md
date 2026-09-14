# Environment Variables

## `frontend/.env.local` (copy from `frontend/.env.local.example`)

| Variable | Where it's used | Secret? |
|---|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase client (browser + server) | No — public by design |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase client (browser + server) | No — RLS protects data, not this key |
| `NEXT_PUBLIC_API_URL` | Calls to the FastAPI backend | No |

## `backend/.env` (copy from `backend/.env.example`)

| Variable | Where it's used | Secret? |
|---|---|---|
| `ENVIRONMENT` | `app/core/config.py` | No |
| `API_PORT` | local dev only | No |
| `ALLOWED_ORIGINS` | CORS | No |
| `SUPABASE_URL` | `app/core/supabase.py` | No (same URL as frontend) |
| `SUPABASE_SERVICE_ROLE_KEY` | `app/core/supabase.py` — bypasses RLS | **Yes — never expose to frontend** |
| `SUPABASE_JWT_SECRET` | `services/auth/verify.py` — verifies user tokens | **Yes** |

Later phases will add `ANTHROPIC_API_KEY` (or another AI provider key) and `SPEECHMA_API_KEY` here — both
stay backend-only, same rule as the two Supabase secrets above.

## Rule of thumb

If a variable name starts with `NEXT_PUBLIC_`, assume it ships to every visitor's browser — only put
things there that are safe to be public. Everything else belongs in `backend/.env` only.
