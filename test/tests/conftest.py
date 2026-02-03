import importlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

sys.path.append(ROOT)
sys.path.append(os.path.join(ROOT, "custom_components", "skolmat"))
sys.path.append(os.path.join(ROOT, "test"))

menu_module = importlib.import_module("custom_components.skolmat.menu")
sys.modules.setdefault("menu", menu_module)
