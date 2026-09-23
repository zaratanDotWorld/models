"""Replace only the C_DETAIL collection and named reference-camera settings, then save the loaded master."""

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sage_scene import BACK_WALL, DINING_DEPTH, DINING_LEFT_FRONT_JOG, DINING_LEFT_INSET, DINING_RIGHT_STEP, DINING_WIDTH, FRONT_WALL, FT, LIVING_DEPTH, LIVING_WIDTH, LIVING_X, SHARED_OPENING_LEFT, SHARED_OPENING_WIDTH, SHARED_WALL, SIDE_WALL, WALL_HEIGHT, point_camera

DETAIL = "C_DETAIL"
AUTHORING = "C_AUTHORING"
ROOT = Path(__file__).resolve().parents[1]
TEXTURES = ROOT / "properties/sage/textures"


def remove_owned():
    for name in [DETAIL, AUTHORING]:
        collection = bpy.data.collections.get(name)
        if collection:
            for obj in list(collection.objects):
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(collection)


def mat(name, color, roughness=0.5, metallic=0.0):
    name = f"C_{name}"
    value = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    value.diffuse_color = (*color, 1)
    value.use_nodes = True
    bsdf = value.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    return value


def texture_mat(name, filename, scale):
    value = mat(name, (0.5, 0.5, 0.5), 0.72)
    nodes = value.node_tree.nodes
    links = value.node_tree.links
    for node in list(nodes):
        if node.type not in {"OUTPUT_MATERIAL", "BSDF_PRINCIPLED"}:
            nodes.remove(node)
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(TEXTURES / filename), check_existing=True)
    tex.image.filepath = f"//textures/{filename}"
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (*scale, 1)
    coords = nodes.new("ShaderNodeTexCoord")
    links.new(coords.outputs["UV"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
    links.new(tex.outputs["Color"], nodes["Principled BSDF"].inputs["Base Color"])
    return value


def box(collection, name, location, size, material, bevel=0.0, parent=None):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = f"C_{name}"
    obj.scale = tuple(value / 2 for value in size)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for source in list(obj.users_collection):
        source.objects.unlink(obj)
    collection.objects.link(obj)
    obj.parent = parent
    obj.data.materials.append(material)
    if bevel:
        modifier = obj.modifiers.new("soft_edges", "BEVEL")
        modifier.width = bevel
        modifier.segments = 3
    return obj


def planar_uv(obj, axes, repeat=2.4384):
    layer = obj.data.uv_layers.active or obj.data.uv_layers.new(name="UVMap")
    for polygon in obj.data.polygons:
        for loop_index in polygon.loop_indices:
            point = obj.matrix_world @ obj.data.vertices[obj.data.loops[loop_index].vertex_index].co
            layer.data[loop_index].uv = (point[axes[0]] / repeat, point[axes[1]] / repeat)


def wall_uv(obj, repeat=2.4384):
    layer = obj.data.uv_layers.active or obj.data.uv_layers.new(name="UVMap")
    for polygon in obj.data.polygons:
        axes = (1, 2) if abs(polygon.normal.x) > abs(polygon.normal.y) else (0, 2)
        for loop_index in polygon.loop_indices:
            point = obj.matrix_world @ obj.data.vertices[obj.data.loops[loop_index].vertex_index].co
            layer.data[loop_index].uv = (point[axes[0]] / repeat, point[axes[1]] / repeat)


def set_box(obj, location, size):
    obj.location = location
    obj.dimensions = size


def set_prism(obj, outline, z0, z1):
    count = len(outline)
    inverse = obj.matrix_world.inverted()
    vertices = [inverse @ Vector((x, y, z0)) for x, y in outline] + [inverse @ Vector((x, y, z1)) for x, y in outline]
    faces = [tuple(reversed(range(count))), tuple(range(count, count * 2))]
    faces += [(index, (index + 1) % count, (index + 1) % count + count, index + count) for index in range(count)]
    mesh = bpy.data.meshes.new(f"{obj.name}_canonical")
    mesh.from_pydata(vertices, [], faces)
    old = obj.data
    materials = list(old.materials)
    obj.data = mesh
    for material in materials:
        mesh.materials.append(material)
    bpy.data.meshes.remove(old)






def framed_window(collection, name, axis, center, width, height, sill, wall_material, wood, glass, parent):
    frame = 0.10
    depth = 0.10
    z = sill + height / 2
    if axis == "x":
        box(collection, f"{name}_glass", (center, FRONT_WALL - 0.02, z), (width, 0.025, height), glass, parent=parent)
        verticals = [center - width / 2, center + width / 2]
        if name == "living_front":
            verticals += [center - width * 0.31, center + width * 0.31]
        for x in verticals:
            segment_height = height / 2 - frame
            for label, segment_z in [("lower", (sill + z) / 2), ("upper", (z + sill + height) / 2)]:
                box(collection, f"{name}_vertical_{x:.2f}_{label}", (x, FRONT_WALL - 0.05, segment_z), (frame, depth, segment_height), wood, parent=parent)
        for zz in [sill, sill + height]:
            box(collection, f"{name}_horizontal_{zz:.2f}", (center, FRONT_WALL - 0.05, zz), (width + frame, depth, frame), wood, parent=parent)
        if name == "living_front":
            for side in [-1, 1]:
                side_center = center + side * width * 0.405
                box(collection, f"{name}_side_rail_{side}", (side_center, FRONT_WALL - 0.05, z), (width * 0.19 + frame, depth, frame), wood, parent=parent)
    else:
        x = LIVING_X + LIVING_WIDTH - 0.02 if "living" in name else LIVING_X + DINING_WIDTH - 0.02
        box(collection, f"{name}_glass", (x, center, z), (0.025, width, height), glass, parent=parent)
        verticals = [center - width / 2, center + width / 2]
        if name == "dining_side_b":
            verticals = verticals[1:]
        for y in verticals:
            segment_height = height / 2 - frame
            for label, segment_z in [("lower", (sill + z) / 2), ("upper", (z + sill + height) / 2)]:
                box(collection, f"{name}_vertical_{y:.2f}_{label}", (x - 0.03, y, segment_z), (depth, frame, segment_height), wood, parent=parent)
        levels = [z] if name.startswith("dining_side") else [sill, sill + height, z]
        rail_width = width if name.startswith("dining_side") else width + frame
        for zz in levels:
            box(collection, f"{name}_horizontal_{zz:.2f}", (x - 0.03, center, zz), (depth, rail_width, frame), wood, parent=parent)






def main():
    if not bpy.data.filepath:
        raise RuntimeError("Load the saved master before applying detail")
    for filename in ["living-wallpaper.webp", "dining-wallpaper.webp"]:
        if not (TEXTURES / filename).is_file():
            raise RuntimeError(f"Missing required texture: {TEXTURES / filename}")
    remove_owned()
    collection = bpy.data.collections.new(DETAIL)
    bpy.data.collections["EXPORT"].children.link(collection)
    authoring = bpy.data.collections.new(AUTHORING)
    bpy.data.collections["AUTHORING"].children.link(authoring)
    living = bpy.data.objects["living"]
    dining = bpy.data.objects["dining"]
    shell = bpy.data.objects["shared_shell"]
    dining_front = FRONT_WALL + LIVING_DEPTH + SHARED_WALL
    dining_back = dining_front + DINING_DEPTH
    dining_left_upper = LIVING_X + DINING_LEFT_INSET
    dining_left_outer = LIVING_X + DINING_LEFT_FRONT_JOG
    dining_left_lower = dining_left_upper
    dining_right = LIVING_X + DINING_WIDTH
    opening_start = LIVING_X + SHARED_OPENING_LEFT
    opening_end = opening_start + SHARED_OPENING_WIDTH
    front_form_width = 1.02
    rear_form_width = 0.40
    front_form_depth = 0.62
    rear_form_depth = 0.51
    outline = [
        (dining_left_lower, dining_front),
        (dining_right - front_form_width, dining_front),
        (dining_right - front_form_width, dining_front + front_form_depth),
        (dining_right, dining_front + front_form_depth),
        (dining_right, dining_back - rear_form_depth),
        (dining_right - rear_form_width, dining_back - rear_form_depth),
        (dining_right - rear_form_width, dining_back),
        (dining_left_upper, dining_back),
        (dining_left_upper, dining_front + 1.18),
        (dining_left_lower, dining_front + 1.18),
    ]
    if bpy.context.scene.get("canonical_layout_revision") != 6:
        floor = bpy.data.objects["floor_dining"]
        ceiling_object = bpy.data.objects["ceiling_dining"]
        set_prism(floor, outline, -0.08, 0.0)
        set_prism(ceiling_object, outline, WALL_HEIGHT, WALL_HEIGHT + 0.08)
        if not floor.data.materials:
            floor.data.materials.append(next(material for material in bpy.data.materials if material.name.split(".")[0] == "woodFloor"))
        if not ceiling_object.data.materials:
            ceiling_object.data.materials.append(bpy.data.materials["ceiling"])
        planar_uv(floor, (1, 0))
        bpy.context.scene["canonical_layout_revision"] = 6
    set_box(bpy.data.objects["shared_wall_left"], ((LIVING_X + opening_start) / 2, FRONT_WALL + LIVING_DEPTH + SHARED_WALL / 2, WALL_HEIGHT / 2), (opening_start - LIVING_X, SHARED_WALL, WALL_HEIGHT))
    shared_right = LIVING_X + LIVING_WIDTH
    set_box(bpy.data.objects["shared_wall_right"], ((opening_end + shared_right) / 2, FRONT_WALL + LIVING_DEPTH + SHARED_WALL / 2, WALL_HEIGHT / 2), (shared_right - opening_end, SHARED_WALL, WALL_HEIGHT))
    set_box(bpy.data.objects["shared_opening_header"], ((opening_start + opening_end) / 2, FRONT_WALL + LIVING_DEPTH + SHARED_WALL / 2, 2.46), (SHARED_OPENING_WIDTH, SHARED_WALL, WALL_HEIGHT - 2.18))
    set_box(bpy.data.objects["shared_opening_threshold"], ((opening_start + opening_end) / 2, FRONT_WALL + LIVING_DEPTH + SHARED_WALL / 2, -0.04), (SHARED_OPENING_WIDTH, SHARED_WALL, 0.08))
    shell["shared_opening_width_m"] = SHARED_OPENING_WIDTH
    shell["shared_opening_left_m"] = SHARED_OPENING_LEFT
    shell["dining_right_step_m"] = DINING_RIGHT_STEP
    shell["canonical_plan_source"] = "design/floor-plans.pdf A2.0 right-hand Proposed First Floor Plan"
    for name in ["wall_living_front", "wall_living_right", "wall_living_left", "wall_dining_right", "wall_dining_back", "wall_dining_left"]:
        bpy.data.objects[name].hide_render = True
        bpy.data.objects[name].hide_viewport = True
    bpy.data.objects["authoring_key"].hide_render = True
    bpy.data.objects["authoring_key"].hide_viewport = True

    plaster = mat("plaster", (0.70, 0.68, 0.59), 0.85)
    oak = mat("oak", (0.32, 0.14, 0.035), 0.38)
    dark_wood = mat("dark_wood", (0.035, 0.010, 0.004), 0.34)
    red = mat("red_textile", (0.27, 0.008, 0.018), 0.78)
    cream = mat("cream_textile", (0.72, 0.67, 0.55), 0.9)
    ceiling = mat("ceiling", (0.72, 0.68, 0.58), 0.95)
    ceiling_bsdf = ceiling.node_tree.nodes["Principled BSDF"]
    floor_wood = mat("floor_wood", (0.055, 0.018, 0.008), 0.42)
    floor_wood_alt = mat("floor_wood_alt", (0.085, 0.030, 0.010), 0.46)
    black = mat("black", (0.018, 0.018, 0.016), 0.35)
    brass = mat("brass", (0.39, 0.22, 0.06), 0.25, 0.65)
    rug = mat("rug", (0.42, 0.16, 0.19), 0.95)
    glass = mat("glass", (0.30, 0.43, 0.44), 0.08)
    glass.diffuse_color = (0.3, 0.43, 0.44, 0.24)
    glass.surface_render_method = "DITHERED"
    glass.node_tree.nodes["Principled BSDF"].inputs["Transmission Weight"].default_value = 0.72
    glass.node_tree.nodes["Principled BSDF"].inputs["IOR"].default_value = 1.45
    cabinet_glass = mat("cabinet_glass", (0.045, 0.038, 0.028), 0.18)
    cabinet_glass.diffuse_color = (0.045, 0.038, 0.028, 0.45)
    cabinet_glass.surface_render_method = "DITHERED"
    cabinet_glass.node_tree.nodes["Principled BSDF"].inputs["Transmission Weight"].default_value = 0.12
    living_wp = texture_mat("living_wallpaper", "living-wallpaper.webp", (1.3, 1.0))
    dining_wp = texture_mat("dining_wallpaper", "dining-wallpaper.webp", (2.2, 1.5))

    for name in ["ceiling_living", "ceiling_dining"]:
        obj = bpy.data.objects[name]
        obj.data.materials.clear()
        obj.data.materials.append(ceiling)
    living_window = 9 * FT
    living_window_center = LIVING_X + LIVING_WIDTH / 2
    left = living_window_center - living_window / 2
    right = living_window_center + living_window / 2
    box(collection, "living_front_wall_left", ((LIVING_X + left) / 2, FRONT_WALL / 2, WALL_HEIGHT / 2), (left - LIVING_X, FRONT_WALL, WALL_HEIGHT), living_wp, parent=shell)
    box(collection, "living_front_wall_right", ((right + LIVING_X + LIVING_WIDTH) / 2, FRONT_WALL / 2, WALL_HEIGHT / 2), (LIVING_X + LIVING_WIDTH - right, FRONT_WALL, WALL_HEIGHT), living_wp, parent=shell)
    box(collection, "living_front_wall_sill", (living_window_center, FRONT_WALL / 2, 0.38), (living_window, FRONT_WALL, 0.76), living_wp, parent=shell)
    box(collection, "living_front_wall_header", (living_window_center, FRONT_WALL / 2, 2.48), (living_window, FRONT_WALL, WALL_HEIGHT - 2.18), living_wp, parent=shell)
    framed_window(collection, "living_front", "x", living_window_center, living_window, 1.58, 0.76, plaster, oak, glass, living)

    dining_front = FRONT_WALL + LIVING_DEPTH + SHARED_WALL
    dining_window_width = (3 + 4 / 12) * FT
    dining_window_midpoint = dining_front + 1.905
    dining_windows = [
        (dining_front + 1.345, dining_window_width),
        (dining_front + 2.465, dining_window_width),
    ]
    side_specs = [
        (living, LIVING_X + LIVING_WIDTH + 0.015, FRONT_WALL, LIVING_DEPTH, living_wp, 0.12, [(FRONT_WALL + 2.52, 4.5 * FT)]),
        (dining, dining_right + 0.015, dining_front + front_form_depth, DINING_DEPTH - front_form_depth - rear_form_depth, dining_wp, 1.72, dining_windows),
    ]
    for room, x, y0, depth, wallpaper, panel_height, windows in side_specs:
        openings = sorted((center - width / 2, center + width / 2) for center, width in windows)
        merged = []
        for start, end in openings:
            if merged and start <= merged[-1][1] + 1e-6:
                merged[-1] = (merged[-1][0], max(merged[-1][1], end))
            else:
                merged.append((start, end))
        solid_spans = []
        cursor = y0
        for start, end in merged:
            if start > cursor:
                solid_spans.append((cursor, start))
            cursor = max(cursor, end)
        if cursor < y0 + depth:
            solid_spans.append((cursor, y0 + depth))
        for index, (start, end) in enumerate(solid_spans):
            box(collection, f"{room.name}_right_panel_{index}", (x, (start + end) / 2, panel_height / 2), (0.03, end - start, panel_height), oak, parent=room)
            box(collection, f"{room.name}_right_wallpaper_{index}", (x - 0.012, (start + end) / 2, panel_height + (WALL_HEIGHT - panel_height) / 2), (0.018, end - start, WALL_HEIGHT - panel_height), wallpaper, parent=room)
            box(collection, f"{room.name}_chair_rail_{index}", (x - 0.025, (start + end) / 2, panel_height), (0.08, end - start, 0.09), oak, 0.015, room)
        for center, width in windows:
            box(collection, f"{room.name}_right_below_{center:.2f}", (x, center, 0.38), (0.03, width, 0.76), oak if room == dining else living_wp, parent=room)
            box(collection, f"{room.name}_right_above_{center:.2f}", (x, center, 2.48), (0.03, width, WALL_HEIGHT - 2.18), wallpaper, parent=room)

    framed_window(collection, "living_side", "y", FRONT_WALL + 2.52, 4.5 * FT, 1.58, 0.76, plaster, oak, glass, living)
    foyer_start, foyer_end = FRONT_WALL + 1.54, FRONT_WALL + 3.49
    for index, (start, end) in enumerate([(FRONT_WALL, foyer_start), (foyer_end, FRONT_WALL + LIVING_DEPTH)]):
        box(collection, f"living_left_wall_{index}", (LIVING_X - SIDE_WALL / 2, (start + end) / 2, WALL_HEIGHT / 2), (SIDE_WALL, end - start, WALL_HEIGHT), living_wp, parent=shell)
    box(collection, "living_foyer_header", (LIVING_X - SIDE_WALL / 2, (foyer_start + foyer_end) / 2, 2.46), (SIDE_WALL, foyer_end - foyer_start, WALL_HEIGHT - 2.18), living_wp, parent=shell)
    for yy in [foyer_start, foyer_end]:
        box(collection, f"living_foyer_trim_{yy:.2f}", (LIVING_X + 0.02, yy, 1.09), (0.12, 0.14, 2.18), oak, 0.015, living)
    dining_back = dining_front + DINING_DEPTH
    kitchen_door_start = LIVING_X + 0.87
    kitchen_door_end = kitchen_door_start + 0.80
    back_center = dining_back + BACK_WALL / 2
    for label, start, end in [("left", dining_left_upper, kitchen_door_start), ("right", kitchen_door_end, dining_right - rear_form_width)]:
        width = end - start
        center = (start + end) / 2
        box(collection, f"dining_rear_{label}_panel", (center, back_center, 0.86), (width, BACK_WALL, 1.72), oak, parent=dining)
        box(collection, f"dining_rear_{label}_wallpaper", (center, back_center, 1.72 + (WALL_HEIGHT - 1.72) / 2), (width, BACK_WALL, WALL_HEIGHT - 1.72), dining_wp, parent=dining)
        box(collection, f"dining_rear_{label}_rail", (center, dining_back - 0.09, 1.72), (width, 0.07, 0.09), oak, 0.015, dining)
    box(collection, "dining_rear_door_header", ((kitchen_door_start + kitchen_door_end) / 2, back_center, 2.45), (kitchen_door_end - kitchen_door_start, BACK_WALL, WALL_HEIGHT - 2.15), dining_wp, parent=dining)
    for xx in [kitchen_door_start, kitchen_door_end]:
        box(collection, f"dining_kitchen_trim_{xx:.2f}", (xx, dining_back - 0.10, 1.08), (0.13, 0.12, 2.16), oak, 0.015, dining)
    box(collection, "dining_kitchen_head_trim", ((kitchen_door_start + kitchen_door_end) / 2, dining_back - 0.10, 2.25), (kitchen_door_end - kitchen_door_start + 0.13, 0.12, 0.14), oak, 0.015, dining)
    dining_foyer_start = dining_front + 0.29
    dining_foyer_end = dining_front + 1.18
    for label, x, start, end in [
        ("front", dining_left_lower, dining_front, dining_foyer_start),
        ("rear", dining_left_upper, dining_foyer_end, dining_back),
    ]:
        box(collection, f"dining_left_{label}_panel", (x + 0.015, (start + end) / 2, 0.86), (0.03, end - start, 1.72), oak, parent=dining)
        box(collection, f"dining_left_{label}_wallpaper", (x + 0.027, (start + end) / 2, 1.72 + (WALL_HEIGHT - 1.72) / 2), (0.018, end - start, WALL_HEIGHT - 1.72), dining_wp, parent=dining)
        box(collection, f"dining_left_{label}_rail", (x + 0.045, (start + end) / 2, 1.72), (0.08, end - start, 0.09), oak, 0.015, dining)
    for label, start, end in [("front", dining_front, dining_foyer_start), ("rear", dining_foyer_end, dining_back)]:
        box(collection, f"dining_left_{label}_wall_core", ((dining_left_outer + dining_left_upper) / 2, (start + end) / 2, WALL_HEIGHT / 2), (dining_left_upper - dining_left_outer, end - start, WALL_HEIGHT), plaster, parent=shell)
    for yy in [dining_foyer_start, dining_foyer_end]:
        box(collection, f"dining_foyer_jamb_{yy:.2f}", (dining_left_lower + 0.05, yy, 1.08), (0.12, 0.13, 2.16), oak, 0.015, dining)
    box(collection, "dining_foyer_head", (dining_left_lower + 0.05, (dining_foyer_start + dining_foyer_end) / 2, 2.25), (0.12, dining_foyer_end - dining_foyer_start + 0.13, 0.14), oak, 0.015, dining)
    for label, width, y0, depth in [("front", front_form_width, dining_front, front_form_depth), ("rear", rear_form_width, dining_back - rear_form_depth, rear_form_depth)]:
        center = (dining_right - width / 2, y0 + depth / 2)
        box(collection, f"dining_right_{label}_form_panel", (*center, 0.86), (width, depth, 1.72), oak, parent=dining)
        box(collection, f"dining_right_{label}_form_wallpaper", (*center, 1.72 + (WALL_HEIGHT - 1.72) / 2), (width, depth, WALL_HEIGHT - 1.72), dining_wp, parent=dining)
    framed_window(collection, "dining_side_a", "y", dining_windows[0][0], dining_windows[0][1], 1.58, 0.76, plaster, oak, glass, dining)
    framed_window(collection, "dining_side_b", "y", dining_windows[1][0], dining_windows[1][1], 1.58, 0.76, plaster, oak, glass, dining)
    dining_frame_x = dining_right - 0.05
    dining_surround_width = dining_window_width * 2 + 0.20
    for zz in [0.76, 2.34]:
        box(collection, f"dining_side_surround_{zz:.2f}", (dining_frame_x, dining_window_midpoint, zz), (0.10, dining_surround_width, 0.10), oak, parent=dining)

    for name in ["shared_wall_left", "shared_wall_right", "shared_opening_header"]:
        obj = bpy.data.objects[name]
        obj.data.materials.clear()
        obj.data.materials.append(plaster)
    opening_start = LIVING_X + SHARED_OPENING_LEFT
    opening_end = opening_start + SHARED_OPENING_WIDTH
    shared_y = FRONT_WALL + LIVING_DEPTH
    for label, start, end in [("left", LIVING_X, opening_start), ("right", opening_end, shared_right)]:
        center = (start + end) / 2
        width = end - start
        box(collection, f"shared_living_{label}_wallpaper", (center, shared_y - 0.008, WALL_HEIGHT / 2), (width, 0.016, WALL_HEIGHT), living_wp, parent=shell)
        box(collection, f"shared_dining_{label}_panel", (center, shared_y + SHARED_WALL + 0.008, 0.86), (width, 0.016, 1.72), oak, parent=shell)
        box(collection, f"shared_dining_{label}_wallpaper", (center, shared_y + SHARED_WALL + 0.008, 1.72 + (WALL_HEIGHT - 1.72) / 2), (width, 0.016, WALL_HEIGHT - 1.72), dining_wp, parent=shell)
    header_height = WALL_HEIGHT - 2.18
    box(collection, "shared_living_header_wallpaper", ((opening_start + opening_end) / 2, shared_y - 0.008, 2.18 + header_height / 2), (SHARED_OPENING_WIDTH, 0.016, header_height), living_wp, parent=shell)
    box(collection, "shared_dining_header_wallpaper", ((opening_start + opening_end) / 2, shared_y + SHARED_WALL + 0.008, 2.18 + header_height / 2), (SHARED_OPENING_WIDTH, 0.016, header_height), dining_wp, parent=shell)
    for trim_x in [opening_start, opening_end]:
        box(collection, f"shared_trim_{trim_x:.2f}", (trim_x, FRONT_WALL + LIVING_DEPTH + SHARED_WALL / 2, 1.09), (0.16, 0.22, 2.18), oak, 0.018, shell)
    box(collection, "shared_head_trim", ((opening_start + opening_end) / 2, shared_y + SHARED_WALL / 2, 2.26), (SHARED_OPENING_WIDTH + 0.16, 0.22, 0.16), oak, 0.018, shell)

    if bpy.data.collections.get("HOUSE_LAYOUT") is None:
        kitchen_depth = 0.85
        kitchen_width = kitchen_door_end - kitchen_door_start
        box(collection, "kitchen_context_floor", (kitchen_door_start + kitchen_width / 2, dining_back + kitchen_depth / 2, 0.01), (kitchen_width, kitchen_depth, 0.02), floor_wood, parent=shell)
        box(collection, "kitchen_context_back", (kitchen_door_start + kitchen_width / 2, dining_back + kitchen_depth, WALL_HEIGHT / 2), (kitchen_width, 0.06, WALL_HEIGHT), plaster, parent=shell)

    for obj in collection.objects:
        materials = set(obj.data.materials) if obj.type == "MESH" else set()
        if living_wp in materials or dining_wp in materials:
            wall_uv(obj)

    table_x = LIVING_X + DINING_WIDTH * 0.56
    table_y = dining_front + DINING_DEPTH * 0.53
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("C_world")
        bpy.context.scene.world = world
        world.color = (0.18, 0.16, 0.13)
        world.use_nodes = True
        background = world.node_tree.nodes.get("Background")
        background.inputs["Color"].default_value = (0.18, 0.16, 0.13, 1)
        background.inputs["Strength"].default_value = 0.32
    for index, (location, energy, size, color) in enumerate([
        ((living_window_center, -0.35, 1.55), 950, 2.2, (0.80, 0.91, 1.0)),
        ((LIVING_X + DINING_WIDTH + 0.35, dining_front + 1.8, 1.55), 800, 2.0, (0.92, 0.86, 0.72)),
        ((table_x, table_y, 2.30), 340, 1.0, (1.0, 0.55, 0.24)),
        ((LIVING_X + LIVING_WIDTH / 2, FRONT_WALL + LIVING_DEPTH / 2, 2.38), 180, 3.0, (0.85, 0.78, 0.66)),
        ((LIVING_X + DINING_WIDTH / 2, dining_front + DINING_DEPTH / 2, 2.38), 160, 3.0, (0.85, 0.74, 0.60)),
    ]):
        data = bpy.data.lights.new(f"C_light_{index}", "AREA")
        data.energy = energy
        data.shape = "DISK"
        data.size = size
        data.color = color
        obj = bpy.data.objects.new(f"C_light_{index}", data)
        authoring.objects.link(obj)
        obj.location = location
        obj.visible_camera = False
        obj.visible_glossy = False
        obj.visible_transmission = False
        if index == 0:
            obj.rotation_euler.x = math.pi / 2
        elif index == 1:
            obj.rotation_euler.y = math.pi / 2
        elif index >= 3:
            obj.rotation_euler.x = math.pi

    cameras = {
        "ref_living_primary": ((7.55, 4.98, 1.58), (7.48, 0.82, 1.02), 108, "photos/house/living.JPG"),
        "ref_living_opening": ((5.55, 1.45, 1.50), (9.10, 4.55, 1.30), 70, "photos/top-360/215-N-Ave-56/02-IMG_7904.jpg"),
        "ref_dining_primary": ((6.30, 5.20, 1.55), (9.5884, 7.4770, 0.5527), 107, "photos/house/dining.JPG"),
        "ref_dining_cabinet": ((5.20, 4.92, 1.48), (7.45, 7.55, 1.24), 70, "photos/top-360/215-N-Ave-56/04-IMG_7910.jpg"),
    }
    for name, (location, target, fov, source) in cameras.items():
        camera = bpy.data.objects[name]
        camera.location = location
        camera.data.sensor_fit = "VERTICAL"
        camera.data.angle_y = math.radians(fov)
        camera["source_reference"] = source
        camera["projection_status"] = "matched starting pose; refine in visual review"
        point_camera(camera, target)

    for name, location, target in [
        ("novel_shared_opening", (8.7, 3.8, 1.65), (7.0, 6.4, 1.2)),
        ("novel_living_corner", (5.25, 1.0, 1.75), (8.4, 3.3, 0.9)),
    ]:
        data = bpy.data.cameras.new(name)
        data.sensor_fit = "VERTICAL"
        data.angle_y = math.radians(70)
        camera = bpy.data.objects.new(name, data)
        authoring.objects.link(camera)
        camera.location = location
        camera.parent = shell
        point_camera(camera, target)

    data = bpy.data.cameras.new("canonical_plan")
    data.type = "ORTHO"
    data.ortho_scale = 10.0
    camera = bpy.data.objects.new("canonical_plan", data)
    authoring.objects.link(camera)
    camera.location = (7.45, 4.25, 14.0)
    camera.parent = shell
    camera.rotation_euler = (0.0, 0.0, 0.0)

    bpy.context.scene["detail_script_ownership"] = "C_DETAIL and C_AUTHORING collections, canonical dining floor and ceiling outline on first migration, base shared-wall geometry, obsolete shell wall visibility flags, ceiling and shared-opening base materials, four reference-camera settings"
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    print(f"Updated detail in {bpy.data.filepath}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
