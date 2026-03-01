import sys
import os

# ── Project root ──
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# ── Conflict-free paths (no duplicate package/module names) ──
sys.path.insert(0, os.path.join(PROJECT_ROOT, "lib", "fantomas", "src"))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "services", "agent", "src"))

# NOTE: backend, orchestrator, fingerprint-provider and proxy-provider
# are handled in their respective conftest.py because they have
# conflicting package/module names (app/, db.py).
