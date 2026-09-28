"""Import the local site GLB and verify its native scale and building placement."""

import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0,str(Path(__file__).resolve().parent))
from sage_site_layout import FT, DETACHED_ALONG, DETACHED_WIDTH, GARAGE_ALONG, GARAGE_WIDTH, PARCEL_LENGTH, PARCEL_WIDTH


def size(name):
    obj=bpy.data.objects[name]; points=[obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    return tuple((max(p[i] for p in points)-min(p[i] for p in points))/FT for i in range(3))


def close(actual,expected,label,tolerance=.03):
    if abs(actual-expected)>tolerance: raise AssertionError(f"{label}: {actual} != {expected}")


def main():
    path=Path(sys.argv[sys.argv.index("--")+1]).resolve()
    bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(path))
    parcel=size("site_ground"); detached=size("site_detached_floor"); garage=size("site_garage_slab")
    close(parcel[0],PARCEL_WIDTH,"parcel width"); close(parcel[1],PARCEL_LENGTH,"parcel length")
    close(detached[0],DETACHED_WIDTH,"detached across"); close(detached[1],DETACHED_ALONG,"detached along")
    close(garage[0],GARAGE_WIDTH,"garage across"); close(garage[1],GARAGE_ALONG,"garage along")
    if any(obj.type in {"CAMERA","LIGHT"} for obj in bpy.data.objects): raise AssertionError("Site GLB contains cameras or lights")
    print(f"Site GLB verified after native reimport: parcel {parcel[0]:.3f} by {parcel[1]:.3f}ft")


if __name__=="__main__":
    try: main()
    except Exception as exc: print(f"ERROR: {exc}",file=sys.stderr); raise
