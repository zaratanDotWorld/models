"""Check and export the detailed rooms plus canonical whole-house layout."""

import hashlib
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_sage_house import main as check_house
from check_sage import main as check_detail


def main():
    check_detail(); check_house()
    source = Path(bpy.data.filepath).resolve()
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    bpy.ops.object.select_all(action="DESELECT")
    for root_name in ["EXPORT", "HOUSE_LAYOUT"]:
        root = bpy.data.collections[root_name]
        for collection in [root, *root.children_recursive]:
            for obj in collection.objects:
                if not obj.hide_viewport: obj.select_set(True)
    out = ROOT / "exports/sage-house-layout"
    out.mkdir(parents=True, exist_ok=True)
    glb = out / "scene.glb"
    bpy.ops.export_scene.gltf(filepath=str(glb), export_format="GLB", use_selection=True, export_cameras=False, export_lights=False, use_visible=True, export_yup=True)
    after = hashlib.sha256(source.read_bytes()).hexdigest()
    if before != after: raise RuntimeError("Read-only export changed the master")
    note = f"""# Sage whole-house layout export

Source scene: `properties/sage/sage.blend`
Source scene SHA-256: `{before}`
Blender version: `{bpy.app.version_string}`
Command: `\"$BLENDER_BIN\" --background properties/sage/sage.blend --python-exit-code 1 --python scripts/export_sage_house.py`

This native GLB combines the existing detailed living/dining export objects with the separately owned canonical two-floor architecture.
It has no browser metadata contract and excludes authoring cameras and render lights.
"""
    (out / "README.md").write_text(note)
    print(f"Exported {glb}; master SHA-256 remained {before}")


if __name__ == "__main__":
    try: main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr); raise
