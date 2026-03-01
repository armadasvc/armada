import sys
import os

# Env vars required by config.py (read when loading the db and checks modules)
os.environ.setdefault("SQL_SERVER_NAME", "test-server")
os.environ.setdefault("SQL_SERVER_USER", "test-user")
os.environ.setdefault("SQL_SERVER_PASSWORD", "test-pass")
os.environ.setdefault("SQL_SERVER_DB", "test-db")

# Clean "db" and "config" modules potentially cached by fingerprint_provider
for _mod in [k for k in sys.modules if k in ("db", "config")]:
    del sys.modules[_mod]

_pp_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "services", "proxy-provider")
)

# Remove the fingerprint-provider path if present
_fp_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "services", "fingerprint-provider")
)
if _fp_path in sys.path:
    sys.path.remove(_fp_path)

if _pp_path not in sys.path:
    sys.path.insert(0, _pp_path)
