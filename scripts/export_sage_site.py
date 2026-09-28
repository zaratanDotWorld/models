"""Check and export the full Sage site without changing the master."""

import hashlib
import sys
from pathlib import Path

import bpy

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from check_sage import main as check_detail
from check_sage_house import main as check_house
from check_sage_site import main as check_site


def main():
    check_detail(); check_house(); check_site()
    source=Path(bpy.data.filepath).resolve(); before=hashlib.sha256(source.read_bytes()).hexdigest()
    bpy.ops.object.select_all(action="DESELECT")
    for root_name in ["EXPORT","HOUSE_LAYOUT","SITE_LAYOUT"]:
        root=bpy.data.collections[root_name]
        for obj in root.all_objects:
            if obj.type in {"MESH","EMPTY"} and not obj.hide_viewport: obj.select_set(True)
    out=ROOT/"exports/sage-site"; out.mkdir(parents=True,exist_ok=True); glb=out/"scene.glb"
    bpy.ops.export_scene.gltf(filepath=str(glb),export_format="GLB",use_selection=True,export_cameras=False,export_lights=False,use_visible=True,export_yup=True)
    after=hashlib.sha256(source.read_bytes()).hexdigest()
    if before!=after: raise RuntimeError("Read-only site export changed the master")
    (out/"README.md").write_text(
        "# Sage site inspection export\n\n"
        f"Source scene SHA-256: `{before}`\n\n"
        "This local GLB combines the preserved detailed rooms, whole-house layout, and separately owned site architecture.\n"
        "It excludes source files, authoring cameras, and render lights.\n"
    )
    print(f"Exported {glb}; master SHA-256 remained {before}")


if __name__=="__main__":
    try: main()
    except Exception as exc: print(f"ERROR: {exc}",file=sys.stderr); raise
