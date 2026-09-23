"""Import the existing tour's two detailed furniture groups into the saved master."""

import os
import sys
import hashlib
import re
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get("SAGE_FURNITURE_GLB", ROOT / ".local/sage-furniture-unbatched.glb"))
COLLECTION = "C_IMPORTED_FURNITURE"
GROUPS = {"Living room furnishings", "Dining room furnishings"}
EXCLUDED = {"livingWallpaper", "diningWallpaper"}
EXCLUDED_GROUPS = {"Television and low console", "Wood spindle dining chair", "Oak wall panel"}
ROUGH_PREFIXES = (
    "C_living_sofa", "C_living_record", "C_living_speaker", "C_living_armchair", "C_living_pouf",
    "C_living_screen", "C_living_sling", "C_living_piano", "C_living_coffee", "C_living_round_rug",
    "C_living_curtain", "C_dining_cabinet", "C_dining_table", "C_dining_bench", "C_dining_chandelier",
    "C_dining_curtain",
)


def descendants(root):
    result = {root}
    pending = list(root.children)
    while pending:
        obj = pending.pop()
        result.add(obj)
        pending.extend(obj.children)
    return result


def object_bounds(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return min(point.y for point in points), max(point.y for point in points)


def position_living_side_curtains(keep):
    window_min, window_max = object_bounds(bpy.data.objects["C_living_side_glass"])
    for name, edge, target in [("Pleated curtain.002", "max", window_min - 0.02), ("Pleated curtain.003", "min", window_max + 0.02)]:
        curtain = next(obj for obj in keep if obj.name == name)
        points = [child.matrix_world @ Vector(corner) for child in curtain.children_recursive if child.type == "MESH" for corner in child.bound_box]
        current = max(point.y for point in points) if edge == "max" else min(point.y for point in points)
        matrix = curtain.matrix_world.copy()
        matrix.translation.y += target - current
        curtain.matrix_world = matrix


def main():
    if not bpy.data.filepath:
        raise RuntimeError("Load the saved master before importing furniture")
    if not SOURCE.is_file():
        raise RuntimeError(f"Missing native furniture export: {SOURCE}")
    old = bpy.data.collections.get(COLLECTION)
    if old:
        for obj in list(old.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(old)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(SOURCE))
    imported = set(bpy.data.objects) - before
    roots = [obj for obj in imported if obj.name in GROUPS]
    if {obj.name for obj in roots} != GROUPS:
        raise RuntimeError("Native export does not contain both named furniture groups")
    keep = set().union(*(descendants(root) for root in roots))
    excluded_groups = [obj for obj in keep if any(obj.name == name or obj.name.startswith(f"{name}.") for name in EXCLUDED_GROUPS)]
    excluded_objects = set().union(*(descendants(root) for root in excluded_groups)) if excluded_groups else set()
    dining_root = next(obj for obj in roots if obj.name == "Dining room furnishings")
    excluded_objects |= {
        obj for obj in dining_root.children
        if obj.type == "MESH"
        and any(material and material.name.split(".")[0] == "oak" for material in obj.data.materials)
        and min(obj.dimensions) < 0.02
    }
    keep -= excluded_objects
    keep = {obj for obj in keep if obj.name not in EXCLUDED}
    keep = {
        obj for obj in keep
        if not (obj.type == "MESH" and any(material and material.name.split(".")[0] in EXCLUDED for material in obj.data.materials))
    }
    collection = bpy.data.collections.new(COLLECTION)
    bpy.data.collections["EXPORT"].children.link(collection)
    for root in roots:
        world = root.matrix_world.copy()
        root.parent = bpy.data.objects["living" if root.name.startswith("Living") else "dining"]
        root.matrix_world = world
    table = next(obj for obj in keep if obj.name == "Long dining table and benches")
    table_world = table.matrix_world.copy()
    table_world.translation.x += 0.7
    table.matrix_world = table_world
    position_living_side_curtains(keep)
    for obj in imported:
        if obj not in keep:
            bpy.data.objects.remove(obj, do_unlink=True)
            continue
        for source in list(obj.users_collection):
            source.objects.unlink(obj)
        collection.objects.link(obj)
    for obj in list(bpy.data.objects):
        if obj.name.startswith(ROUGH_PREFIXES):
            bpy.data.objects.remove(obj, do_unlink=True)
    used_materials = {material for obj in keep if obj.type == "MESH" for material in obj.data.materials if material}
    texture_root = ROOT / "properties/sage/textures"
    texture_root.mkdir(parents=True, exist_ok=True)
    written = set()
    for material in used_materials:
        if not material.use_nodes:
            continue
        for node in material.node_tree.nodes:
            image = getattr(node, "image", None)
            if image is None or image in written or not image.packed_file:
                continue
            label = re.sub(r"[^a-z0-9]+", "-", material.name.lower()).strip("-")
            path = texture_root / f"tour-{label}.png"
            image.filepath_raw = str(path)
            image.file_format = "PNG"
            image.save()
            image.unpack(method="REMOVE")
            image.filepath = f"//textures/{path.name}"
            written.add(image)
    bpy.context.scene["imported_furniture_source"] = SOURCE.name
    bpy.context.scene["imported_furniture_source_sha256"] = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    print(f"Imported {len(keep)} editable objects into {COLLECTION}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
