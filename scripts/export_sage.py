import hashlib
import json
import subprocess
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_sage import main as check_scene

OUTPUT = ROOT / "exports/sage-living-dining"


def main():
    check_scene()
    export_collection = bpy.data.collections.get("EXPORT")
    if export_collection is None:
        raise RuntimeError("Missing EXPORT collection")

    bpy.ops.object.select_all(action="DESELECT")
    for collection in [export_collection, *export_collection.children_recursive]:
        for obj in collection.objects:
            if not obj.hide_viewport:
                obj.select_set(True)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    glb = OUTPUT / "scene.glb"
    bpy.ops.export_scene.gltf(
        filepath=str(glb),
        export_format="GLB",
        use_selection=True,
        export_cameras=True,
        export_lights=False,
        use_visible=True,
        export_yup=True,
    )
    metadata = {
        "asset": "scene.glb",
        "floor_node": "ground_floor",
        "ceiling_nodes": ["ceiling_living", "ceiling_dining"],
        "overview_camera": "overview",
        "rooms": [
            {"id": "living", "floor": 0, "node": "living", "camera": "walk_living", "neighbors": ["dining"]},
            {"id": "dining", "floor": 0, "node": "dining", "camera": "walk_dining", "neighbors": ["living"]},
        ],
    }
    (OUTPUT / "scene.json").write_text(json.dumps(metadata, indent=2) + "\n")
    source_scene = Path(bpy.data.filepath).resolve()
    if not source_scene.is_file():
        raise RuntimeError("Export requires a saved source scene")
    master_hash = hashlib.sha256(source_scene.read_bytes()).hexdigest()
    source_master = bpy.context.scene.get("source_master", str(source_scene))
    source_master_hash = bpy.context.scene.get("source_master_sha256", master_hash)
    web_copy_changes = bpy.context.scene.get("web_copy_changes", "none; exported directly from the saved master")
    try:
        source_label = source_scene.relative_to(ROOT)
    except ValueError:
        source_label = source_scene
    try:
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        revision = "unavailable"
    note = f"""# Sage living and dining export

Source scene: `{source_label}`
Source scene SHA-256: `{master_hash}`
Source master: `{source_master}`
Source master SHA-256: `{source_master_hash}`
Repository revision: `{revision}`
Blender version: `{bpy.app.version_string}`
Command: `\"$BLENDER_BIN\" --background properties/sage/sage.blend --python-exit-code 1 --python scripts/export_sage.py`

This export contains the detailed living and dining reconstruction, native meter scale, Y-up conversion, named room groups, and walkthrough cameras.
Reference cameras, render lights, and source photographs remain authoring-only data outside the GLB.
Web-copy changes: {web_copy_changes}.
Native glTF materials use the browser's lighting and tone mapping, so glass, reflections, and procedural Cycles shading differ from the comparison renders.
"""
    (OUTPUT / "README.md").write_text(note)
    print(f"Exported {glb}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
