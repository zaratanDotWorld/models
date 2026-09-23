"""Render read-only whole-house ground, upper, and axonometric evidence."""

import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sage_house_layout import GROUND_ROOMS, UPPER_ROOMS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "renders/sage-house-layout"


def point(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def labels(rooms, elevation):
    created = []
    display = {"bath-lower-back":"Bath1","bath-lower-front":"Bath2","bath-upper-back":"Bath3","bath-upper-middle":"Bath4"}
    for name, outline in rooms.items():
        if name == "deck":
            continue
        data = bpy.data.curves.new(f"tmp_label_{name}", "FONT")
        data.body = display.get(name,name)
        data.align_x = "CENTER"
        data.align_y = "CENTER"
        data.size = .30
        obj = bpy.data.objects.new(f"tmp_label_{name}", data)
        bpy.context.scene.collection.objects.link(obj)
        obj.location = (sum(x for x,_ in outline)/len(outline)*.3048, sum(y for _,y in outline)/len(outline)*.3048, elevation+.06)
        created.append(obj)
    return created


def render(name, location, target=None, ortho=None, upper=False):
    camera_data = bpy.data.cameras.new(f"tmp_{name}")
    camera = bpy.data.objects.new(f"tmp_{name}", camera_data)
    bpy.context.scene.collection.objects.link(camera)
    camera.location = location
    if ortho:
        camera_data.type = "ORTHO"; camera_data.ortho_scale = ortho; camera.rotation_euler = (0,0,0)
    else:
        point(camera, target); camera_data.lens = 46
    scene = bpy.context.scene
    scene.camera = camera
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.show_shadows = False
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "BOTH"
    if name in {"ground-plan", "upper-plan"}:
        scene.render.resolution_x = 1400; scene.render.resolution_y = 2200
    else:
        scene.render.resolution_x = 1400; scene.render.resolution_y = 1100
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(OUT / f"{name}.png")
    saved = {obj: obj.hide_render for obj in bpy.data.objects}
    temporary = []
    if name in {"ground-plan", "upper-plan"}:
        temporary = labels(UPPER_ROOMS if upper else GROUND_ROOMS, 10*.3048 if upper else 0)
        for obj in bpy.data.objects:
            ancestor = obj
            while ancestor and ancestor.name != "upper_floor": ancestor = ancestor.parent
            if obj.type not in {"MESH", "EMPTY", "FONT"}: obj.hide_render = True
            elif "ceiling" in obj.name or "_header_" in obj.name: obj.hide_render = True
            elif obj.type == "FONT": pass
            elif name == "ground-plan" and ancestor: obj.hide_render = True
            elif name == "upper-plan" and not ancestor and not obj.name.startswith("layout_stair_"): obj.hide_render = True
    elif name in {"house-axon","house-rear-axon"}:
        for obj in bpy.data.objects:
            if "ceiling" in obj.name:
                obj.hide_render = True
    try:
        bpy.ops.render.render(write_still=True)
    finally:
        for obj, hidden in saved.items(): obj.hide_render = hidden
        for obj in temporary:
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.curves.remove(data)
        bpy.data.objects.remove(camera, do_unlink=True); bpy.data.cameras.remove(camera_data)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    center = ((-0.358+32.681)/2*.3048, 24.4*.3048)
    render("ground-plan", (center[0],center[1],22), ortho=17.4)
    render("upper-plan", (center[0],center[1],22), ortho=17.4, upper=True)
    render("house-axon", (18,-12,16), (center[0],center[1],2.7))
    render("house-rear-axon", (-12,22,15), (center[0],center[1],2.7))
    (OUT / "index.html").write_text("""<!doctype html><meta charset=\"utf-8\"><title>Sage canonical layout comparison</title>
<style>body{font:16px system-ui;margin:24px;background:#eee;color:#222}main{max-width:1500px;margin:auto}.pair{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:24px 0}.pair img{width:100%;height:auto;background:#777}.key{columns:2} @media(max-width:800px){.pair{grid-template-columns:1fr}.key{columns:1}}</style>
<main><h1>Sage canonical layout comparison</h1><p>The right-hand A2.0 and A2.1 drawings govern the modeled architecture.</p>
<section class=\"pair\"><figure><img src=\"../../.local/canonical-ground-complete.png\"><figcaption>Source A2.0 right-hand ground floor.</figcaption></figure><figure><img src=\"ground-plan.png\"><figcaption>Native model ground-floor cutaway.</figcaption></figure></section>
<section class=\"pair\"><figure><img src=\"../../.local/canonical-upper-complete.png\"><figcaption>Source A2.1 right-hand upper floor.</figcaption></figure><figure><img src=\"upper-plan.png\"><figcaption>Native model upper-floor cutaway.</figcaption></figure></section>
<h2>Room key</h2><div class=\"key\"><p>Ground: room-1 = BED3, room-2 = BED1, room-3 = BED2.</p><p>Ground: Bath1 = rear bathroom and Bath2 = front bathroom.</p><p>Upper: room-4 through room-7 = BED4 through BED7.</p><p>Upper: room-8 = BED10, room-9 = BED9, room-10 = BED8.</p><p>Upper: Bath3 = rear bathroom and Bath4 = middle bathroom.</p><p>Neutral rooms remain unfurnished in this layout pass.</p></div>
<h2>Whole-house cutaways</h2><section class=\"pair\"><img src=\"house-axon.png\"><img src=\"house-rear-axon.png\"></section><p>The rear view shows the upper deck and rear facade setback.</p><p>The rear deck extent and exterior step heights are inferred where the plan does not print dimensions.</p></main>""")
    print(f"Rendered whole-house evidence in {OUT}")


if __name__ == "__main__":
    try: main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr); raise
