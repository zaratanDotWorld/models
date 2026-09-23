"""Read-only checks for the canonical two-floor Sage layout."""

import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sage_house_layout import GROUND_HEIGHT, GROUND_ROOMS, GROUND_WALLS, UPPER_ROOMS, UPPER_WALLS, UPPER_Z


def bounds(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return tuple((min(p[i] for p in points), max(p[i] for p in points)) for i in range(3))


def main():
    layout = bpy.data.collections.get("HOUSE_LAYOUT")
    export = bpy.data.collections.get("EXPORT")
    if not layout or not export:
        raise RuntimeError("Missing HOUSE_LAYOUT or EXPORT")
    layout_objects = {obj for collection in [layout, *layout.children_recursive] for obj in collection.objects}
    export_objects = {obj for collection in [export, *export.children_recursive] for obj in collection.objects}
    overlap = layout_objects & export_objects
    if overlap:
        raise RuntimeError(f"HOUSE_LAYOUT leaked into EXPORT: {sorted(obj.name for obj in overlap)[:3]}")
    upper = bpy.data.objects.get("upper_floor")
    if upper is None or abs(upper["floor_elevation_m"] - UPPER_Z * .3048) > 1e-6:
        raise RuntimeError("Upper floor elevation is not 10 feet")
    for name in [*GROUND_ROOMS, *UPPER_ROOMS]:
        obj = bpy.data.objects.get(name)
        if obj is None:
            raise RuntimeError(f"Missing room node {name}")
        expected = upper if name in UPPER_ROOMS else bpy.data.objects["ground_floor"]
        if obj.parent != expected:
            raise RuntimeError(f"Wrong floor parent for {name}")
        floor = bpy.data.objects.get(f"layout_{name}_floor")
        ceiling = bpy.data.objects.get(f"layout_{name}_ceiling")
        if not floor or floor.parent != obj or (name not in {"deck","foyer"} and (not ceiling or ceiling.parent != obj)):
            raise RuntimeError(f"Missing grouped floor or ceiling for {name}")
        if name == "foyer" and sum(item.name.startswith("layout_foyer_ceiling_") and item.parent == obj for item in layout_objects) != 3:
            raise RuntimeError("Foyer ceiling must remain split around the stairwell")
        if name == "deck" and ceiling:
            raise RuntimeError("Outdoor deck must not have an indoor ceiling")
        floor_top = bounds(floor)[2][1]
        expected_top = UPPER_Z * .3048 if name in UPPER_ROOMS else 0.0
        if abs(floor_top - expected_top) > 1e-6:
            raise RuntimeError(f"Finished floor elevation changed for {name}")
    if not any(obj.name.startswith("layout_stair_lower_") for obj in layout_objects) or not any(obj.name.startswith("layout_stair_upper_") for obj in layout_objects):
        raise RuntimeError("Both stair flights are required")
    stair_top = max(bounds(obj)[2][1] for obj in layout_objects if obj.name.startswith("layout_stair_upper_"))
    if abs(stair_top - UPPER_Z * .3048) > 1e-6:
        raise RuntimeError("Upper stair does not meet the finished floor")
    assembly_bottom = (GROUND_HEIGHT + .08) * .3048
    assembly_top = (UPPER_Z - .08) * .3048
    for name in UPPER_ROOMS:
        assembly = bpy.data.objects.get(f"layout_floor_assembly_{name}")
        if name == "deck":
            if assembly: raise RuntimeError("Outdoor deck must not receive the indoor floor assembly")
            continue
        if not assembly or assembly.parent != upper:
            raise RuntimeError(f"Missing inter-floor assembly below {name}")
        z = bounds(assembly)[2]
        if abs(z[0]-assembly_bottom)>1e-6 or abs(z[1]-assembly_top)>1e-6:
            raise RuntimeError(f"Inter-floor assembly elevation changed below {name}")
    if any(obj.name.startswith("C_kitchen_context_") and (not obj.hide_viewport or not obj.hide_render) for obj in bpy.data.objects):
        raise RuntimeError("Shallow kitchen context must remain hidden")
    for name in ["layout_ground_plan", "layout_upper_plan", "layout_house_axon"]:
        camera = bpy.data.objects.get(name)
        if not camera or camera.type != "CAMERA" or camera.name not in bpy.data.collections["HOUSE_LAYOUT_CAMERAS"].objects:
            raise RuntimeError(f"Missing authoring layout camera {name}")
    expected_thresholds = sum(opening["kind"] != "window" for wall in [*GROUND_WALLS,*UPPER_WALLS] for opening in wall.get("apertures",[])) + 3
    actual_thresholds = sum(obj.name.startswith("layout_threshold_") for obj in layout_objects)
    if actual_thresholds != expected_thresholds:
        raise RuntimeError(f"Expected {expected_thresholds} complete thresholds, found {actual_thresholds}")
    if bpy.data.objects.get("utility-basement-access") is None:
        raise RuntimeError("Missing rear utility-basement access context")
    if sum(obj.name.startswith("layout_utility_access_step_") for obj in layout_objects) != 3:
        raise RuntimeError("Rear utility-basement access context must include three visible inferred steps")
    for name in ["living", "dining", "Living room furnishings", "Dining room furnishings"]:
        if bpy.data.objects.get(name) is None:
            raise RuntimeError(f"Detailed room object lost: {name}")
    print(f"Whole-house layout verified: {len(GROUND_ROOMS)} ground room nodes, {len(UPPER_ROOMS)} upper room nodes, 10ft upper elevation")


if __name__ == "__main__":
    try: main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr); raise
