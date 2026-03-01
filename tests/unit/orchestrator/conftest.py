import sys
import os

# Clean the "app" package potentially cached by backend tests
_to_remove = [key for key in sys.modules if key == "app" or key.startswith("app.")]
for key in _to_remove:
    del sys.modules[key]

_orchestrator_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "services", "orchestrator")
)

# Remove the backend path if present
_backend_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "services", "backend")
)
if _backend_path in sys.path:
    sys.path.remove(_backend_path)

if _orchestrator_path not in sys.path:
    sys.path.insert(0, _orchestrator_path)
