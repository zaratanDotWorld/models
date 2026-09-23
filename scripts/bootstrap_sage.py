import math
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sage_scene import (
    BACK_WALL,
    DINING_DEPTH,
    DINING_RIGHT_STEP,
    DINING_WIDTH,
    FT,
    FRONT_WALL,
    LIVING_DEPTH,
    LIVING_WIDTH,
    LIVING_X,
    SHARED_OPENING_LEFT,
    SHARED_OPENING_WIDTH,
    SHARED_WALL,
    SIDE_WALL,
    WALL_HEIGHT,
    camera,
    cube,
    empty,
    material,
)

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "properties/sage/sage.blend"


def main():
    if MASTER.exists():
        raise RuntimeError(f"Refusing to overwrite existing master: {MASTER}")

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.length_unit = "METERS"
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100

    export = bpy.data.collections.new("EXPORT")
    authoring = bpy.data.collections.new("AUTHORING")
    scene.collection.children.link(export)
    scene.collection.children.link(authoring)

    floor = empty("ground_floor", collection=export)
    living = empty("living", parent=floor, collection=export)
    dining = empty("dining", parent=floor, collection=export)
    shell = empty("shared_shell", parent=floor, collection=export)
    floor["units"] = "meters"
    floor["origin"] = "exterior front-left plan corner"
    living["interior_width_m"] = LIVING_WIDTH
    living["interior_depth_m"] = LIVING_DEPTH
    dining["interior_depth_m"] = DINING_DEPTH
    dining["width_basis"] = "inferred from plan and prototype; verify during camera matching"
    shell["shared_opening_width_m"] = SHARED_OPENING_WIDTH
    shell["dining_right_step_m"] = DINING_RIGHT_STEP

    wood = material("wood_floor", (0.23, 0.10, 0.045))
    wall_mat = material("warm_plaster", (0.73, 0.66, 0.52))
    ceiling_mat = material("ceiling", (0.82, 0.80, 0.73))

    shared_front = FRONT_WALL + LIVING_DEPTH
    dining_front = shared_front + SHARED_WALL
    dining_back = dining_front + DINING_DEPTH
    cube("floor_living", (LIVING_X + LIVING_WIDTH / 2, FRONT_WALL + LIVING_DEPTH / 2, -0.04), (LIVING_WIDTH, LIVING_DEPTH, 0.08), living, wood)
    cube("floor_dining", (LIVING_X + DINING_WIDTH / 2, dining_front + DINING_DEPTH / 2, -0.04), (DINING_WIDTH, DINING_DEPTH, 0.08), dining, wood)

    right_living = LIVING_X + LIVING_WIDTH
    right_dining = LIVING_X + DINING_WIDTH
    cube("wall_living_front", (LIVING_X + LIVING_WIDTH / 2, FRONT_WALL / 2, WALL_HEIGHT / 2), (LIVING_WIDTH, FRONT_WALL, WALL_HEIGHT), shell, wall_mat)
    cube("wall_living_right", (right_living + SIDE_WALL / 2, FRONT_WALL + LIVING_DEPTH / 2, WALL_HEIGHT / 2), (SIDE_WALL, LIVING_DEPTH, WALL_HEIGHT), shell, wall_mat)
    cube("wall_dining_right", (right_dining + SIDE_WALL / 2, dining_front + DINING_DEPTH / 2, WALL_HEIGHT / 2), (SIDE_WALL, DINING_DEPTH, WALL_HEIGHT), shell, wall_mat)
    cube("wall_dining_back", (LIVING_X + DINING_WIDTH / 2, dining_back + BACK_WALL / 2, WALL_HEIGHT / 2), (DINING_WIDTH, BACK_WALL, WALL_HEIGHT), shell, wall_mat)
    cube("wall_living_left", (LIVING_X - SIDE_WALL / 2, FRONT_WALL + LIVING_DEPTH / 2, WALL_HEIGHT / 2), (SIDE_WALL, LIVING_DEPTH, WALL_HEIGHT), shell, wall_mat)
    cube("wall_dining_left", (LIVING_X - SIDE_WALL / 2, dining_front + DINING_DEPTH / 2, WALL_HEIGHT / 2), (SIDE_WALL, DINING_DEPTH, WALL_HEIGHT), shell, wall_mat)

    opening_start = LIVING_X + SHARED_OPENING_LEFT
    opening_end = opening_start + SHARED_OPENING_WIDTH
    cube("shared_wall_left", ((LIVING_X + opening_start) / 2, shared_front + SHARED_WALL / 2, WALL_HEIGHT / 2), (opening_start - LIVING_X, SHARED_WALL, WALL_HEIGHT), shell, wall_mat)
    cube("shared_wall_right", ((opening_end + right_dining) / 2, shared_front + SHARED_WALL / 2, WALL_HEIGHT / 2), (right_dining - opening_end, SHARED_WALL, WALL_HEIGHT), shell, wall_mat)
    cube("shared_opening_header", ((opening_start + opening_end) / 2, shared_front + SHARED_WALL / 2, 8.5 * FT), (SHARED_OPENING_WIDTH, SHARED_WALL, 1.0 * FT), shell, wall_mat)
    cube("shared_opening_threshold", ((opening_start + opening_end) / 2, shared_front + SHARED_WALL / 2, -0.04), (SHARED_OPENING_WIDTH, SHARED_WALL, 0.08), shell, wood)

    cube("ceiling_living", (LIVING_X + LIVING_WIDTH / 2, FRONT_WALL + LIVING_DEPTH / 2, WALL_HEIGHT), (LIVING_WIDTH, LIVING_DEPTH, 0.06), floor, ceiling_mat)
    cube("ceiling_dining", (LIVING_X + DINING_WIDTH / 2, dining_front + DINING_DEPTH / 2, WALL_HEIGHT), (DINING_WIDTH, DINING_DEPTH, 0.06), floor, ceiling_mat)

    walk_living = camera("walk_living", (23 * FT, 13 * FT, 5.3 * FT), (24 * FT, 5 * FT, 4.5 * FT), living, export)
    walk_dining = camera("walk_dining", (18.2 * FT, 17.2 * FT, 5.3 * FT), (27 * FT, 22 * FT, 4.5 * FT), dining, export)
    overview = camera("overview", (25 * FT, 13 * FT, 50 * FT), (25 * FT, 14 * FT, 0), floor, export, 48)

    reference_root = empty("reference_cameras", collection=authoring)
    for name, loc, target, fov in [
        ("ref_living_primary", (19 * FT, 14 * FT, 5 * FT), (25 * FT, 4 * FT, 4.5 * FT), 86),
        ("ref_living_opening", (29 * FT, 7 * FT, 5 * FT), (20 * FT, 17 * FT, 4.5 * FT), 74),
        ("ref_dining_primary", (18 * FT, 16 * FT, 5 * FT), (27 * FT, 23 * FT, 4.5 * FT), 86),
        ("ref_dining_cabinet", (29 * FT, 25 * FT, 5 * FT), (19 * FT, 22 * FT, 4.5 * FT), 74),
    ]:
        camera(name, loc, target, reference_root, authoring, fov)

    key = bpy.data.lights.new("authoring_key", "AREA")
    key.energy = 900
    key.shape = "DISK"
    key.size = 5
    key_obj = bpy.data.objects.new("authoring_key", key)
    authoring.objects.link(key_obj)
    key_obj.location = (24 * FT, 12 * FT, 8 * FT)
    scene.camera = walk_living
    scene["bootstrap_ownership"] = "Initial scene only; refuses to overwrite the master."
    scene["inferred_geometry"] = "Dining width, shared opening placement, wall and ceiling heights require camera matching."
    MASTER.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(MASTER))
    print(f"Created {MASTER}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
