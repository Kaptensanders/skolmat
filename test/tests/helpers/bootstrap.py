import importlib
import os
import sys


def _ensure_path(path: str) -> None:
    if path not in sys.path:
        sys.path.insert(0, path)


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

_ensure_path(ROOT)
_ensure_path(os.path.join(ROOT, "custom_components", "skolmat"))
_ensure_path(os.path.join(ROOT, "test"))

menu_module = importlib.import_module("custom_components.skolmat.menu")
sys.modules.setdefault("menu", menu_module)
