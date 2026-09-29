"""Render the local comparison gallery for the complete Sage exterior."""

import hashlib
import os
import shutil
from pathlib import Path

import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"renders/sage-exterior-completion"
PAIRS=[
    ("front-regression","photos/top-360/215-N-Ave-56/14-IMG_7952.jpg","site_exterior_front","wide","Current built condition"),
    ("rear-regression","photos/top-360/215-N-Ave-56/18-IMG_7964.jpg","site_exterior_rear_stairs","wide","Pre-renovation patio and stair reference; current plans govern apertures"),
    ("rear-patio-pre-renovation","photos/top-360/215-N-Ave-56/19-IMG_7966.jpg","site_exterior_rear_support","wide","Pre-renovation openings; current plans govern apertures"),
    ("south-side-pre-renovation","photos/renovation/IMG_5058.JPG","site_exterior_south_reference","portrait","Pre-renovation openings; current plans govern apertures"),
    ("detached-pre-renovation","photos/top-360/213-N-Ave-56/46-IMG_1631.jpg","site_exterior_detached","wide","Pre-renovation openings; 2023 A2.3 governs apertures"),
    ("garage","photos/top-360/215-N-Ave-56/22-IMG_7982.jpg","site_exterior_garage","wide","Photographed courtyard-facing doors"),
]


def render(camera_name,target,aspect=None):
    scene=bpy.context.scene
    scene.camera=bpy.data.objects[camera_name]
    if camera_name=="site_exterior_rear_patio":
        scene.camera.location=Vector((10,55.75,3.1))*.3048
        aim=Vector((10,50,3.1))*.3048
        scene.camera.rotation_euler=(aim-scene.camera.location).to_track_quat("-Z","Y").to_euler()
        scene.camera.data.type="ORTHO"
        scene.camera.data.ortho_scale=25*.3048
        scene.render.engine="BLENDER_WORKBENCH"
        scene.display.shading.light="STUDIO"
        scene.display.shading.color_type="MATERIAL"
        scene.display.shading.show_shadows=True
        scene.display.shading.show_cavity=True
        scene.display.shading.cavity_type="BOTH"
        scene.display.shading.show_object_outline=True
    if aspect=="portrait":
        scene.render.resolution_x=800
        scene.render.resolution_y=1200
    elif aspect=="wide":
        scene.render.resolution_x=1400
        scene.render.resolution_y=800
    elif aspect=="studio":
        scene.render.resolution_x=1500
        scene.render.resolution_y=1000
    else:
        scene.render.resolution_x=1200
        scene.render.resolution_y=800
    scene.render.resolution_percentage=100
    scene.render.filepath=str(target)
    bpy.ops.render.render(write_still=True)


def main():
    reference_root=os.environ.get("SAGE_REFERENCE_ROOT")
    if not reference_root:
        raise RuntimeError("SAGE_REFERENCE_ROOT is required")
    master=Path(bpy.data.filepath).resolve()
    before=hashlib.sha256(master.read_bytes()).hexdigest()
    OUT.mkdir(parents=True,exist_ok=True)
    scene=bpy.context.scene
    scene.render.engine="BLENDER_EEVEE_NEXT"
    scene.render.image_settings.file_format="PNG"
    scene.view_settings.look="AgX - Medium High Contrast"
    scene.world.color=(.35,.38,.44)
    if scene.world.use_nodes:
        background=next((node for node in scene.world.node_tree.nodes if node.type=="BACKGROUND"),None)
        if background:
            background.inputs["Color"].default_value=(.45,.50,.60,1)
            background.inputs["Strength"].default_value=.65
    for light in [obj for obj in scene.objects if obj.type=="LIGHT"]:
        light.hide_render=True
    bpy.ops.object.light_add(type="SUN",location=(0,0,25))
    sun=bpy.context.object
    sun.rotation_euler=(.72,-.48,-.62)
    sun.data.energy=1.4
    sun.data.angle=.16
    cards=[]
    for label,relative_source,camera_name,aspect,note in PAIRS:
        source=Path(reference_root)/relative_source
        if not source.is_file():
            raise RuntimeError(f"Missing source reference: {source}")
        source_name=f"source-{label}{source.suffix.lower()}"
        model_name=f"model-{label}.png"
        shutil.copy2(source,OUT/source_name)
        render(camera_name,OUT/model_name,aspect)
        cards.append(f'<section><h2>{label.replace("-"," ").title()}</h2><p>{note}</p><figure><img src="{source_name}"><figcaption>Private source copy</figcaption></figure><figure><img src="{model_name}"><figcaption>Model view</figcaption></figure></section>')
    for label,camera_name,aspect in [
        ("north-side","site_exterior_north",None),
        ("south-side","site_exterior_south",None),
        ("roof","site_main_roof_plan","portrait"),
        ("circulation","site_exterior_circulation",None),
        ("rear-patio-closeup-diagnostic","site_exterior_rear_patio","studio"),
    ]:
        model_name=f"model-{label}.png"
        render(camera_name,OUT/model_name,aspect)
        caption="Studio geometry diagnostic" if aspect=="studio" else "Unobstructed geometry diagnostic"
        cards.append(f'<section><h2>{label.replace("-"," ").title()}</h2><figure><img src="{model_name}"><figcaption>{caption}</figcaption></figure></section>')
    note="Plans govern building dimensions and revised openings. Older photographs establish fixed material and eave character only where renovation changed doors or windows. Rear window 207.2 remains absent and existing 207.3 remains present. Unprinted roof, garage-height, paving-edge and grade dimensions remain estimated."
    html='<!doctype html><meta charset="utf-8"><title>Sage exterior completion</title><style>body{font:16px system-ui;background:#eee;color:#222;margin:2rem}section{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin:2rem 0}h2,section>p{grid-column:1/-1}figure{background:white;padding:1rem;margin:0}img{width:100%;height:560px;object-fit:contain}figcaption{margin-top:.5rem}@media(max-width:900px){section{grid-template-columns:1fr}}</style><h1>Sage exterior completion</h1><p>'+note+'</p>'+''.join(cards)
    (OUT/"index.html").write_text(html)
    after=hashlib.sha256(master.read_bytes()).hexdigest()
    if before!=after:
        raise RuntimeError("Read-only exterior render changed the master")
    print(f"Rendered {len(PAIRS)} comparison pairs to {OUT}; master SHA-256 remained {before}")


if __name__=="__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}")
        raise
