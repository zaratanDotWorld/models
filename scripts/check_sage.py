import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sage_scene import DINING_DEPTH, DINING_LEFT_FRONT_JOG, DINING_LEFT_INSET, DINING_RIGHT_STEP, LIVING_DEPTH, LIVING_WIDTH, LIVING_X, SHARED_OPENING_LEFT, SHARED_OPENING_WIDTH, SHARED_WALL


def require(name):
    matches = [obj for obj in bpy.data.objects if obj.name == name]
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one object named {name}, found {len(matches)}")
    return matches[0]


def bounds(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return min(point.x for point in points), max(point.x for point in points), min(point.y for point in points), max(point.y for point in points)


def main():
    required = ["ground_floor", "living", "dining", "ceiling_living", "ceiling_dining", "walk_living", "walk_dining", "overview"]
    objects = {name: require(name) for name in required}
    export = bpy.data.collections.get("EXPORT")
    export_objects = {obj.name for collection in [export, *export.children_recursive] for obj in collection.objects} if export else set()
    if any(obj.name not in export_objects for obj in objects.values()):
        raise RuntimeError("Required export nodes must belong to the EXPORT collection")
    if objects["living"].parent != objects["ground_floor"] or objects["dining"].parent != objects["ground_floor"]:
        raise RuntimeError("Room nodes must be direct children of ground_floor")
    if objects["ceiling_living"].parent != objects["ground_floor"] or objects["ceiling_dining"].parent != objects["ground_floor"]:
        raise RuntimeError("Ceilings must be direct children of ground_floor")
    detail = bpy.data.collections.get("C_DETAIL")
    authoring = bpy.data.collections.get("C_AUTHORING")
    web_copy = bool(bpy.context.scene.get("source_master_sha256"))
    if detail is None or authoring is None or detail.name not in {item.name for item in export.children_recursive}:
        if detail is None or detail.name not in {item.name for item in export.children_recursive} or not web_copy:
            raise RuntimeError("Detailed geometry must belong to EXPORT/C_DETAIL")
    authoring_root = bpy.data.collections.get("AUTHORING")
    authoring_objects = {obj.name for collection in [authoring_root, *authoring_root.children_recursive] for obj in collection.objects} if authoring_root else set()
    if authoring and any(obj.name in export_objects for obj in authoring.objects):
        raise RuntimeError("Comparison cameras and render lights must remain outside EXPORT")
    for obj in detail.objects:
        if obj.type != "MESH":
            continue
        ancestor = obj
        while ancestor and ancestor.name != "ground_floor":
            ancestor = ancestor.parent
        if ancestor is None:
            raise RuntimeError(f"Detailed mesh does not inherit from ground_floor: {obj.name}")
    imported = bpy.data.collections.get("C_IMPORTED_FURNITURE")
    if imported is None or imported.name not in {item.name for item in export.children_recursive}:
        raise RuntimeError("Detailed furniture must belong to EXPORT/C_IMPORTED_FURNITURE")
    for name in ["Living room furnishings", "Dining room furnishings"]:
        if name not in {obj.name for obj in imported.objects}:
            raise RuntimeError(f"Missing imported furniture group: {name}")
    if require("Living room furnishings").parent != objects["living"] or require("Dining room furnishings").parent != objects["dining"]:
        raise RuntimeError("Imported furniture groups must belong to their room nodes")
    if any(obj.type == "MESH" and any(material and material.name.split(".")[0] in {"livingWallpaper", "diningWallpaper"} for material in obj.data.materials) for obj in imported.objects):
        raise RuntimeError("Imported prototype wall skins must not duplicate the authoritative shell")
    if any(obj.parent and obj.parent.name == "Dining room furnishings" and obj.type == "MESH" and min(obj.dimensions) < 0.02 and any(material and material.name.split(".")[0] == "oak" for material in obj.data.materials) for obj in imported.objects):
        raise RuntimeError("Imported prototype oak wall skins must not duplicate the authoritative shell")
    for name in ["C_living_front_glass", "C_living_side_glass", "C_dining_side_a_glass", "C_dining_side_b_glass"]:
        require(name)
    if not web_copy:
        for name in ["ref_living_primary", "ref_living_opening", "ref_dining_primary", "ref_dining_cabinet", "novel_shared_opening", "novel_living_corner", "canonical_plan"]:
            camera = require(name)
            if camera.type != "CAMERA" or name not in authoring_objects:
                raise RuntimeError(f"{name} must be an authoring camera")
    for name in ["wall_living_front", "wall_living_right", "wall_living_left", "wall_dining_right", "wall_dining_back", "wall_dining_left"]:
        if not require(name).hide_viewport:
            raise RuntimeError(f"Obsolete solid wall {name} must remain excluded from export")
    texture_root = Path(__file__).resolve().parents[1] / "properties/sage/textures"
    for name in ["living-wallpaper.webp", "dining-wallpaper.webp"]:
        if not (texture_root / name).is_file():
            raise RuntimeError(f"Missing required texture: {texture_root / name}")
    living_width = bounds(require("C_living_right_panel_0"))[0] - bounds(require("C_living_left_wall_0"))[1]
    living_depth = bounds(require("shared_wall_left"))[2] - bounds(require("C_living_front_wall_left"))[3]
    dining_depth = bounds(require("C_dining_rear_right_panel"))[2] - bounds(require("shared_wall_left"))[3]
    if abs(living_width - LIVING_WIDTH) > 1e-6 or abs(living_depth - LIVING_DEPTH) > 1e-6:
        raise RuntimeError("Living wall faces do not match the A2.0 interior span")
    if abs(dining_depth - DINING_DEPTH) > 1e-6:
        raise RuntimeError("Dining wall faces do not match the A2.0 interior depth")
    shell = require("shared_shell")
    if abs(shell["shared_opening_width_m"] - SHARED_OPENING_WIDTH) > 1e-6:
        raise RuntimeError("Shared opening width changed")
    if abs(shell["dining_right_step_m"] - DINING_RIGHT_STEP) > 1e-6:
        raise RuntimeError("Dining outward step changed")
    threshold = bounds(require("shared_opening_threshold"))
    if abs(threshold[0] - (LIVING_X + SHARED_OPENING_LEFT)) > 1e-6 or abs((threshold[1] - threshold[0]) - SHARED_OPENING_WIDTH) > 1e-6:
        raise RuntimeError("Shared opening does not match the canonical plan trace")
    if abs((bounds(require("shared_wall_left"))[3] - bounds(require("shared_wall_left"))[2]) - SHARED_WALL) > 1e-6:
        raise RuntimeError("Shared wall thickness does not match the canonical plan trace")
    living_wall = require("C_living_right_panel_0")
    dining_wall = require("C_dining_right_panel_0")
    living_outer = bounds(living_wall)[1]
    dining_outer = bounds(dining_wall)[1]
    if abs((dining_outer - living_outer) - DINING_RIGHT_STEP) > 1e-6:
        raise RuntimeError("Dining outward step geometry changed")
    living_left = bounds(require("C_living_left_wall_0"))[1]
    dining_upper_left = bounds(require("C_dining_left_rear_panel"))[0]
    dining_lower_left = bounds(require("C_dining_left_front_panel"))[0]
    if abs((dining_upper_left - living_left) - DINING_LEFT_INSET) > 1e-6:
        raise RuntimeError("Dining rear-left inset does not match the canonical plan trace")
    if abs((dining_lower_left - living_left) - DINING_LEFT_INSET) > 1e-6:
        raise RuntimeError("Dining lower-left interior face does not match the canonical plan trace")
    living_opening = bounds(require("C_living_left_wall_1"))[2] - bounds(require("C_living_left_wall_0"))[3]
    dining_opening = bounds(require("C_dining_left_rear_panel"))[2] - bounds(require("C_dining_left_front_panel"))[3]
    if abs(living_opening - 1.95) > 1e-6 or abs(dining_opening - 0.89) > 1e-6:
        raise RuntimeError("Foyer openings do not match the canonical plan trace")
    for name, width, depth in [("C_dining_right_front_form", 1.02, 0.62), ("C_dining_right_rear_form", 0.40, 0.51)]:
        measured = bounds(require(f"{name}_panel"))
        if abs((measured[1] - measured[0]) - width) > 1e-6 or abs((measured[3] - measured[2]) - depth) > 1e-6:
            raise RuntimeError(f"Dining corner form does not match the canonical plan trace: {name}")
        require(f"{name}_wallpaper")
    floor = require("floor_dining")
    if not floor.data.materials:
        raise RuntimeError("Dining floor must retain its authored material")
    floor_xy = {(round((floor.matrix_world @ vertex.co).x, 4), round((floor.matrix_world @ vertex.co).y, 4)) for vertex in floor.data.vertices}
    expected_xy = {
        (round(LIVING_X + DINING_LEFT_INSET, 4), round(bounds(require("shared_wall_left"))[3], 4)),
        (round(LIVING_X + LIVING_WIDTH + DINING_RIGHT_STEP, 4), round(bounds(require("shared_wall_left"))[3] + 0.62, 4)),
        (round(LIVING_X + LIVING_WIDTH + DINING_RIGHT_STEP - 0.40, 4), round(bounds(require("shared_wall_left"))[3] + DINING_DEPTH, 4)),
    }
    if not expected_xy.issubset(floor_xy):
        raise RuntimeError("Dining floor outline does not follow the canonical corner forms")
    hit, _, _, _, hit_object, _ = bpy.context.scene.ray_cast(bpy.context.evaluated_depsgraph_get(), Vector((5.15, 5.3832, 1.3)), Vector((-1.0, 0.0, 0.0)), distance=1.0)
    if hit:
        raise RuntimeError(f"Dining-to-foyer opening is blocked by {hit_object.name}")
    living_window_min = 0.1524 + 2.52 - 4.5 * 0.3048 / 2
    living_window_max = 0.1524 + 2.52 + 4.5 * 0.3048 / 2
    for name, edge, target in [("Pleated curtain.002", "max", living_window_min - 0.02), ("Pleated curtain.003", "min", living_window_max + 0.02)]:
        curtain = require(name)
        points = [child.matrix_world @ Vector(corner) for child in curtain.children_recursive if child.type == "MESH" for corner in child.bound_box]
        measured = max(point.y for point in points) if edge == "max" else min(point.y for point in points)
        if abs(measured - target) > 1e-5:
            raise RuntimeError(f"Living side-window curtain does not follow its canonical jamb: {name}")
    for name in ["walk_living", "walk_dining"]:
        camera = objects[name]
        if camera.type != "CAMERA" or camera.data.type != "PERSP":
            raise RuntimeError(f"{name} must be a perspective camera")
        if camera.data.sensor_fit != "VERTICAL" or abs(math.degrees(camera.data.angle_y) - 75) > 0.01:
            raise RuntimeError(f"{name} must retain a 75-degree vertical field of view")
    print("Scene structure, measured span, inferred landmarks, and cameras verified")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
