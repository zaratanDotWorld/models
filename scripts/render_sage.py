import os
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "renders/reconstruction"

CAMERAS = {
    "ref_living_primary": (480, 640),
    "ref_living_opening": (640, 427),
    "ref_dining_primary": (480, 640),
    "ref_dining_cabinet": (640, 427),
    "novel_shared_opening": (640, 400),
    "novel_living_corner": (640, 400),
    "canonical_plan": (1000, 900),
}


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT" if os.environ.get("SAGE_RENDER_ENGINE") == "BLENDER_EEVEE_NEXT" else "CYCLES"
    scene.cycles.samples = int(os.environ.get("SAGE_RENDER_SAMPLES", "32"))
    scene.cycles.use_denoising = True
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    requested = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else list(CAMERAS)
    scale = int(os.environ.get("SAGE_RENDER_SCALE", "1"))
    if scale < 1:
        raise RuntimeError("SAGE_RENDER_SCALE must be a positive integer")
    unknown = [name for name in requested if name not in CAMERAS]
    if unknown:
        raise RuntimeError(f"Unknown render cameras: {', '.join(unknown)}")
    for name in requested:
        engine_before = scene.render.engine
        visibility_before = {obj: obj.hide_render for obj in bpy.data.objects}
        camera = bpy.data.objects.get(name)
        if camera is None or camera.type != "CAMERA":
            raise RuntimeError(f"Missing required camera: {name}")
        scene.camera = camera
        width, height = CAMERAS[name]
        scene.render.resolution_x, scene.render.resolution_y = width * scale, height * scale
        for ceiling_name in ["ceiling_living", "ceiling_dining"]:
            bpy.data.objects[ceiling_name].hide_render = name in {"novel_living_corner", "canonical_plan"}
        upper = bpy.data.objects.get("upper_floor")
        if upper:
            for obj in [upper, *upper.children_recursive]:
                obj.hide_render = True
        if name == "canonical_plan":
            scene.render.engine = "BLENDER_WORKBENCH"
            scene.display.shading.light = "STUDIO"
            scene.display.shading.color_type = "MATERIAL"
            scene.display.shading.show_shadows = True
            scene.display.shading.show_cavity = True
            for obj in bpy.data.objects:
                if "header" in obj.name.lower() or "head" in obj.name.lower():
                    obj.hide_render = True
            for object_name in ["floor_living", "floor_dining", "shared_opening_threshold"]:
                bpy.data.objects[object_name].hide_render = True
        imported = bpy.data.collections.get("C_IMPORTED_FURNITURE")
        if imported:
            for obj in imported.objects:
                obj.hide_render = name == "canonical_plan"
        scene.render.filepath = str(OUTPUT / f"{name}.png")
        try:
            bpy.ops.render.render(write_still=True)
            print(f"Rendered {scene.render.filepath}")
        finally:
            scene.render.engine = engine_before
            for obj, hidden in visibility_before.items():
                obj.hide_render = hidden


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
