import sys
import os

# Env vars required by config.py (read when loading the db module)
os.environ.setdefault("SQL_SERVER_NAME", "test-server")
os.environ.setdefault("SQL_SERVER_USER", "test-user")
os.environ.setdefault("SQL_SERVER_PASSWORD", "test-pass")
os.environ.setdefault("SQL_SERVER_DB", "test-db")

_fp_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "services", "fingerprint-provider")
)
if _fp_path not in sys.path:
    sys.path.insert(0, _fp_path)
