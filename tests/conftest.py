"""
Makes both the repo root (for `services.*`) and `backend/` (for `app.*`)
importable for every test under `tests/`, regardless of which directory
pytest is invoked from.

Without this, `tests/backend/test_chat.py` and `test_health.py` only put
`backend/` on sys.path (to import `app.main`), which is enough on its own
only as long as nothing under `app` reaches into `services` — that stopped
being true once `backend/app/api/v1/chat.py` added `from services.ai import
...`. `services/` lives at the repo root, a sibling of `backend/`, so it
needs its own sys.path entry; individual test files each doing this by
hand (as `tests/services/test_prompt_loader.py` did) is easy to miss, so
it's centralized here instead. pytest imports every `conftest.py` before
collecting the test files in its directory tree, so this runs first.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

for path in (ROOT, ROOT / "backend"):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)
