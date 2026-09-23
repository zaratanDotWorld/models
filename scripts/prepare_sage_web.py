"""Create a disposable web-export copy without changing the loaded Sage master."""

import hashlib
import sys
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / ".local/sage-web.blend"


def main():
    source = Path(bpy.data.filepath).resolve()
    if not source.is_file():
        raise RuntimeError("Load the saved Sage master before preparing the web copy")
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    export = bpy.data.collections.get("EXPORT")
    if export is None:
        raise RuntimeError("Missing EXPORT collection")
    keep = {obj for collection in [export, *export.children_recursive] for obj in collection.objects}
    for obj in list(bpy.data.objects):
        if obj not in keep:
            bpy.data.objects.remove(obj, do_unlink=True)
    for collection in list(bpy.data.collections):
        if collection != export and collection.name not in {item.name for item in export.children_recursive}:
            bpy.data.collections.remove(collection)
    bpy.context.scene["source_master"] = str(source.relative_to(ROOT))
    bpy.context.scene["source_master_sha256"] = source_hash
    bpy.context.scene["web_copy_changes"] = "authoring-only objects removed and unused data purged; geometry and materials retained"
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    print(f"Prepared {OUTPUT} from {source_hash}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
