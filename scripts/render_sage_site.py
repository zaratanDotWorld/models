"""Render the architecture-focused Sage site gallery without saving the master."""

import hashlib
import subprocess
import sys
from pathlib import Path

import bpy

ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"renders/sage-site-layout"
VIEWS=["site_plan","site_perspective_front","site_perspective_rear","site_main_front","site_main_rear","site_main_roof_plan","site_detached_plan"]


def render(camera_name, filename):
    scene=bpy.context.scene; scene.camera=bpy.data.objects[camera_name]
    if camera_name in {"site_plan","site_main_roof_plan"}: scene.render.resolution_x,scene.render.resolution_y=650,900
    else: scene.render.resolution_x,scene.render.resolution_y=900,650
    scene.render.filepath=str(OUT/filename); bpy.ops.render.render(write_still=True)


def render_pdf(pdf, page, filename):
    prefix=OUT/filename.removesuffix(".png")
    subprocess.run(["pdftoppm","-f",str(page),"-l",str(page),"-singlefile","-r","120","-png",str(pdf),str(prefix)],check=True)


def main():
    source=Path(bpy.data.filepath).resolve(); before=hashlib.sha256(source.read_bytes()).hexdigest(); OUT.mkdir(parents=True,exist_ok=True)
    scene=bpy.context.scene; scene.render.engine="BLENDER_WORKBENCH"; scene.render.resolution_x=900; scene.render.resolution_y=650; scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"; scene.display.shading.light="STUDIO"; scene.display.shading.show_shadows=True; scene.display.shading.show_cavity=True; scene.display.shading.cavity_type="BOTH"
    for name in VIEWS:
        roofs=bpy.data.collections["SITE_ROOFS"]
        roofs.hide_render=name=="site_detached_plan"
        hidden=[]
        if name=="site_detached_plan":
            hidden=[obj for obj in bpy.data.collections["SITE_LAYOUT"].all_objects if obj.name.startswith("site_detached_") and "_header_" in obj.name]
            for obj in hidden: obj.hide_render=True
        render(name,f"{name}.png")
        for obj in hidden: obj.hide_render=False
    bpy.data.collections["SITE_ROOFS"].hide_render=False
    sources={
      "source-site-plan.png":(ROOT/"properties/sage/plans/site-plan.pdf",1),
      "source-main-roof.png":(ROOT/"properties/sage/plans/roof-plan.pdf",1),
      "source-main-elevations.png":(ROOT/"properties/sage/plans/elevations.pdf",1),
      "source-detached.png":(ROOT/"properties/sage/plans/detached-unit.pdf",3),
    }
    for name,(pdf,page) in sources.items(): render_pdf(pdf,page,name)
    cards=[]
    for name in VIEWS: cards.append(f'<figure><img src="{name}.png"><figcaption>{name.replace("_"," ")}</figcaption></figure>')
    for name in sources: cards.append(f'<figure><img src="{name}"><figcaption>{name.replace("-"," ").replace(".png","")}</figcaption></figure>')
    (OUT/"index.html").write_text("<!doctype html><meta charset=utf-8><title>Sage site architecture</title><style>body{font:16px system-ui;background:#eee;color:#222;margin:2rem}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:1rem}figure{background:white;padding:1rem;margin:0}img{width:100%;height:420px;object-fit:contain}figcaption{text-transform:capitalize;margin-top:.5rem}</style><h1>Sage full-site architecture review</h1><p>Model views are paired with repository-sanitized drawing excerpts. Main-house floor cutaways are in <a href=\"../sage-house-layout/index.html\">the whole-house gallery</a>.</p><main>"+"".join(cards)+"</main>")
    after=hashlib.sha256(source.read_bytes()).hexdigest()
    if before!=after: raise RuntimeError("Read-only render changed the master")
    print(f"Rendered {len(VIEWS)} site views to {OUT}; master SHA-256 remained {before}")


if __name__=="__main__":
    try: main()
    except Exception as exc: print(f"ERROR: {exc}",file=sys.stderr); raise
