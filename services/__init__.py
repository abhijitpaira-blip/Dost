"""
DOST services — one package per capability. The backend imports from here;
these packages hold the actual business logic so backend/app stays a thin
HTTP layer.

Phase 1 status: every package below is a stub (docstring + placeholder) except
`auth`, which has real Supabase-auth helpers. Later phases fill each in without
touching this top-level structure.
"""
