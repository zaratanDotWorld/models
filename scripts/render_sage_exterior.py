"""Render the private local front and rear exterior comparison gallery."""

import hashlib
import os
import shutil
from pathlib import Path

import bpy

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"renders/sage-exterior-details"
PAIRS=[
    ("front","photos/top-360/215-N-Ave-56/14-IMG_7952.jpg","site_exterior_front"),
    ("porch","photos/top-360/215-N-Ave-56/17-IMG_7961.jpg","site_exterior_porch"),
    ("rear-stairs","photos/top-360/215-N-Ave-56/18-IMG_7964.jpg","site_exterior_rear_stairs"),
    ("rear-support","photos/top-360/215-N-Ave-56/19-IMG_7966.jpg","site_exterior_rear_support"),
]


def render(camera_name, target):
    scene=bpy.context.scene
    scene.camera=bpy.data.objects[camera_name]
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
    sun=bpy.context.object; sun.rotation_euler=(.72,-.48,-.62); sun.data.energy=1.4; sun.data.angle=.16
    cards=[]
    for label,relative_source,camera_name in PAIRS:
        source=Path(reference_root)/relative_source
        if not source.is_file():
            raise RuntimeError(f"Missing source reference: {source}")
        source_name=f"source-{label}{source.suffix.lower()}"
        model_name=f"model-{label}.png"
        shutil.copy2(source,OUT/source_name)
        render(camera_name,OUT/model_name)
        cards.append(f'<section><h2>{label.replace("-"," ").title()}</h2><figure><img src="{source_name}"><figcaption>Private source copy</figcaption></figure><figure><img src="{model_name}"><figcaption>Model view</figcaption></figure></section>')
    for label,camera_name in [("front-diagnostic","site_exterior_front_diagnostic"),("rear-diagnostic","site_exterior_rear_diagnostic")]:
        model_name=f"model-{label}.png"
        render(camera_name,OUT/model_name)
        cards.append(f'<section><h2>{label.replace("-"," ").title()}</h2><figure><img src="{model_name}"><figcaption>Unobstructed geometry diagnostic</figcaption></figure></section>')
    note="Canonical drawings govern wall and aperture positions except rear window 207.2, which A3.1 marks as new but the owner confirmed was not built and photos 18 and 21 show as blank wall. The model retains existing window 207.3. A2.1 fixes the narrow side deck; the rear platform extent and photographed stair are inferred from A2.0 post marks and photos 18, 19, 21 and 26. Member sizes and camera poses are inferred."
    html='<!doctype html><meta charset="utf-8"><title>Sage exterior details</title><style>body{font:16px system-ui;background:#eee;color:#222;margin:2rem}section{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin:2rem 0}h2{grid-column:1/-1}figure{background:white;padding:1rem;margin:0}img{width:100%;height:560px;object-fit:contain}figcaption{margin-top:.5rem}@media(max-width:900px){section{grid-template-columns:1fr}}</style><h1>Sage front and rear exterior comparisons</h1><p>'+note+'</p>'+''.join(cards)
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
