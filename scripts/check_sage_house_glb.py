"""Import the whole-house GLB into a clean scene and check its native hierarchy."""

import sys
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from sage_house_layout import GROUND_HEIGHT, GROUND_ROOMS, UPPER_ROOMS, UPPER_Z


def bounds(obj):
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return tuple((min(point[index] for point in points), max(point[index] for point in points)) for index in range(3))


def mesh_tree(objects):
    vertices = []
    polygons = []
    owners = []
    for obj in objects:
        offset = len(vertices)
        vertices.extend(obj.matrix_world @ vertex.co for vertex in obj.data.vertices)
        for face in obj.data.polygons:
            polygons.append(tuple(offset + index for index in face.vertices))
            owners.append(obj.name)
    return BVHTree.FromPolygons(vertices,polygons,all_triangles=False), owners


def main():
    path = Path(sys.argv[sys.argv.index("--") + 1]) if "--" in sys.argv else ROOT / "exports/sage-house-layout/scene.glb"
    two_room = path.parent.name == "sage-living-dining"
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(path))
    if two_room:
        if bpy.data.objects.get("upper_floor") or bpy.data.objects.get("room-1"):
            raise RuntimeError("Whole-house objects leaked into the two-room GLB")
        for name in ["ground_floor", "living", "dining", "walk_living", "walk_dining"]:
            if bpy.data.objects.get(name) is None: raise RuntimeError(f"Two-room GLB missing {name}")
        print(f"Two-room GLB containment verified: {len(bpy.data.objects)} objects")
        return
    required = ["ground_floor", "upper_floor", "living", "dining", *GROUND_ROOMS, *UPPER_ROOMS]
    missing = [name for name in required if bpy.data.objects.get(name) is None]
    if missing: raise RuntimeError(f"Imported GLB missing {missing}")
    if bpy.data.objects["upper_floor"].parent is not None:
        raise RuntimeError("upper_floor must remain a root")
    if bpy.data.objects["room-10"].parent != bpy.data.objects["upper_floor"]:
        raise RuntimeError("Upper room hierarchy was not retained")
    if bpy.data.objects["living"].parent != bpy.data.objects["ground_floor"]:
        raise RuntimeError("Detailed ground room hierarchy was not retained")
    for name in GROUND_ROOMS:
        if bpy.data.objects[name].parent != bpy.data.objects["ground_floor"]:
            raise RuntimeError(f"Ground room hierarchy was not retained for {name}")
    for name in UPPER_ROOMS:
        if bpy.data.objects[name].parent != bpy.data.objects["upper_floor"]:
            raise RuntimeError(f"Upper room hierarchy was not retained for {name}")
    ground_top = bounds(bpy.data.objects["layout_room-1_floor"])[2][1]
    upper_top = bounds(bpy.data.objects["layout_room-4_floor"])[2][1]
    if abs(ground_top) > 1e-5 or abs(upper_top - UPPER_Z * .3048) > 1e-5:
        raise RuntimeError("Imported finished-floor datums changed")
    room1 = bounds(bpy.data.objects["layout_room-1_floor"])
    expected_width = (15.60-.10)*.3048
    if abs((room1[0][1]-room1[0][0])-expected_width) > 1e-4:
        raise RuntimeError("Imported BED3 measured width changed")
    images = [image for image in bpy.data.images if image.packed_file]
    if len(images) < 9 or any(min(image.size) <= 0 for image in images):
        raise RuntimeError("Embedded detailed-room textures did not reimport")
    assembly = [obj for obj in bpy.data.objects if obj.type == "MESH" and obj.name.startswith("layout_floor_assembly_")]
    if len(assembly) != 28:
        raise RuntimeError(f"Expected 28 inter-floor assembly meshes, found {len(assembly)}")
    band = ((GROUND_HEIGHT+.08)*.3048,(UPPER_Z-.08)*.3048)
    if any(abs(bounds(obj)[2][0]-band[0])>1e-5 or abs(bounds(obj)[2][1]-band[1])>1e-5 for obj in assembly):
        raise RuntimeError("Imported inter-floor assembly elevation changed")
    tree, owners = mesh_tree(assembly)
    hit, normal, index, distance = tree.ray_cast(Vector((35*.3048,40*.3048,9.5*.3048)),Vector((-1,0,0)),5*.3048)
    if hit is None:
        raise RuntimeError("Imported east facade remains open through the floor assembly")
    stair_hit = tree.ray_cast(Vector((6*.3048,18*.3048,10.1*.3048)),Vector((0,0,-1)),1.2*.3048)[0]
    if stair_hit is not None:
        raise RuntimeError("Imported floor assembly blocks the A2.1 stair opening")
    print(f"Native GLB reimport verified: {len(bpy.data.objects)} objects, {len(images)} embedded images, 0m and {UPPER_Z*.3048:.3f}m floor datums")


if __name__ == "__main__":
    try: main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr); raise
