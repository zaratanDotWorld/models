"""Small native-Blender helpers for explicitly scheduled house geometry."""

import math

import bpy
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

from sage_scene import FT


def owned_collection(name, parent=None):
    old = bpy.data.collections.get(name)
    if old:
        for child in list(old.children):
            remove_collection(child)
        for obj in list(old.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(old)
    collection = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(collection)
    return collection


def remove_collection(collection):
    for child in list(collection.children):
        remove_collection(child)
    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(collection)


def link_only(obj, collection):
    for source in list(obj.users_collection):
        source.objects.unlink(obj)
    collection.objects.link(obj)


def empty(collection, name, parent=None):
    obj = bpy.data.objects.new(name, None)
    collection.objects.link(obj)
    obj.parent = parent
    return obj


def prism(collection, name, outline_ft, bottom_ft, top_ft, parent, material=None):
    """Create a concave-safe vertical prism with its top at the finished-floor datum."""
    area = sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(outline_ft, outline_ft[1:] + outline_ft[:1]))
    if area < 0:
        outline_ft = list(reversed(outline_ft))
    ring = [Vector((x * FT, y * FT, 0)) for x, y in outline_ft]
    triangles = tessellate_polygon([ring])
    index = {(round(vertex.x, 9), round(vertex.y, 9)): position for position, vertex in enumerate(ring)}
    count = len(ring)
    vertices = [(v.x, v.y, bottom_ft * FT) for v in ring] + [(v.x, v.y, top_ft * FT) for v in ring]
    faces = []
    for triangle in triangles:
        base = tuple(vertex if isinstance(vertex, int) else index[(round(vertex.x, 9), round(vertex.y, 9))] for vertex in triangle)
        faces.append(tuple(reversed(base)))
        faces.append(tuple(position + count for position in base))
    faces.extend((i, (i + 1) % count, (i + 1) % count + count, i + count) for i in range(count))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.validate(verbose=True)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.parent = parent
    if material:
        obj.data.materials.append(material)
    return obj


def wall_piece(collection, name, start_ft, end_ft, bottom_ft, top_ft, thickness_ft, parent, material=None):
    x1, y1 = start_ft
    x2, y2 = end_ft
    length = math.hypot(x2 - x1, y2 - y1)
    if length <= 0 or top_ft <= bottom_ft:
        return None
    bpy.ops.mesh.primitive_cube_add(location=((x1 + x2) * FT / 2, (y1 + y2) * FT / 2, (bottom_ft + top_ft) * FT / 2))
    obj = bpy.context.object
    obj.name = name
    obj.scale = (length * FT / 2, thickness_ft * FT / 2, (top_ft - bottom_ft) * FT / 2)
    obj.rotation_euler.z = math.atan2(y2 - y1, x2 - x1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    link_only(obj, collection)
    obj.parent = parent
    if material:
        obj.data.materials.append(material)
    return obj


def wall_with_apertures(collection, spec, floor_ft, height_ft, parent, material=None, thickness_ft=5 / 12):
    """Build one scheduled wall; aperture offsets are measured from the wall start in feet."""
    start = Vector(spec["start"])
    end = Vector(spec["end"])
    direction = end - start
    length = direction.length
    if length <= 0:
        raise ValueError(f"Wall {spec['id']} has no length")
    direction.normalize()
    apertures = sorted(spec.get("apertures", []), key=lambda value: value["start"])
    cursor = 0.0
    objects = []
    for index, opening in enumerate(apertures):
        opening_start = float(opening["start"])
        opening_end = float(opening["end"])
        if opening_start < cursor - 1e-6 or opening_end <= opening_start or opening_end > length + 1e-6:
            raise ValueError(f"Wall {spec['id']} has overlapping or out-of-range apertures")
        opening_start = max(cursor, opening_start)
        opening_end = min(length, opening_end)
        if opening_start > cursor:
            objects.append(wall_piece(collection, f"{spec['id']}_solid_{index}", start + direction * cursor, start + direction * opening_start, floor_ft, floor_ft + height_ft, thickness_ft, parent, material))
        bottom = floor_ft + float(opening.get("bottom", 0))
        top = floor_ft + float(opening.get("top", 7))
        if bottom > floor_ft:
            objects.append(wall_piece(collection, f"{spec['id']}_sill_{index}", start + direction * opening_start, start + direction * opening_end, floor_ft, bottom, thickness_ft, parent, material))
        if top < floor_ft + height_ft:
            objects.append(wall_piece(collection, f"{spec['id']}_header_{index}", start + direction * opening_start, start + direction * opening_end, top, floor_ft + height_ft, thickness_ft, parent, material))
        cursor = opening_end
    if cursor < length:
        objects.append(wall_piece(collection, f"{spec['id']}_solid_end", start + direction * cursor, end, floor_ft, floor_ft + height_ft, thickness_ft, parent, material))
    return [obj for obj in objects if obj]
