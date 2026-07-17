bl_info = {
    "name": "GTA Scene Rebuilder",
    "author": "Bigbigdog",
    "version": (1, 1, 0),
    "blender": (5, 1, 0),
    "location": "View3D > Sidebar > GTA Tools",
    "description": "Skeleton addon for rebuilding GTA scenes.",
    "doc_url": "https://github.com/Vakhrush/GTA-Scene-Rebuilder",
    "category": "3D View",
}

import importlib
import sys
from pathlib import Path

if __package__:
    from . import operator, panel, preferences
else:
    import importlib.util

    def _load_local_module(module_name):
        module_path = Path(__file__).with_name(f"{module_name}.py")
        spec = importlib.util.spec_from_file_location(f"gta_scene_rebuilder_{module_name}", module_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    preferences = _load_local_module("preferences")
    operator = _load_local_module("operator")
    panel = _load_local_module("panel")


modules = (
    preferences,
    operator,
    panel,
)


def register():
    for module in modules:
        importlib.reload(module)

    for module in modules:
        module.register()


def unregister():
    for module in reversed(modules):
        module.unregister()


if __name__ == "__main__":
    register()
