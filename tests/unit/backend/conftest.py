import sys
import os

_backend_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "services", "backend")
)
if _backend_path not in sys.path:
    sys.path.insert(0, _backend_path)
