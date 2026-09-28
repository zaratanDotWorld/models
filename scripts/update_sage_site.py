"""Replace the separately owned full-site architecture in the loaded Sage master."""

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sage_house_builder import empty, owned_collection, prism, wall_piece, wall_with_apertures
from sage_house_layout import GROUND_WALLS, UPPER_WALLS
from sage_scene import FT
from sage_site_layout import *

OWNED = "SITE_LAYOUT"
CAMERAS = "SITE_LAYOUT_CAMERAS"
ROOFS = "SITE_ROOFS"


def material(name, color, roughness=0.75):
    value = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    value.diffuse_color = (*color, 1)
    value.roughness = roughness
    return value


def mesh(collection, name, vertices_ft, faces, parent, mat):
    data = bpy.data.meshes.new(name)
    data.from_pydata([(x * FT, y * FT, z * FT) for x, y, z in vertices_ft], [], faces)
    data.validate(verbose=True)
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.parent = parent
    obj.data.materials.append(mat)
    return obj


def beam3d(collection, name, start_ft, end_ft, thickness_ft, parent, mat):
    start=Vector(tuple(v*FT for v in start_ft)); end=Vector(tuple(v*FT for v in end_ft)); delta=end-start
    bpy.ops.mesh.primitive_cube_add(location=(start+end)/2)
    obj=bpy.context.object; obj.name=name; obj.scale=(thickness_ft*FT/2,thickness_ft*FT/2,delta.length/2)
    obj.rotation_euler=delta.to_track_quat("Z","Y").to_euler(); bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for source in list(obj.users_collection): source.objects.unlink(obj)
    collection.objects.link(obj); obj.parent=parent; obj.data.materials.append(mat); return obj


def gable_roof(collection, name, x1, x2, y1, y2, eave, ridge, parent, mat, ridge_along_y=True, overhang=.7):
    x1 -= overhang; x2 += overhang; y1 -= overhang; y2 += overhang
    if ridge_along_y:
        mid = (x1 + x2) / 2
        verts = [(x1,y1,eave),(x1,y2,eave),(mid,y1,ridge),(mid,y2,ridge),(x2,y1,eave),(x2,y2,eave)]
        faces = [(0,1,3,2),(2,3,5,4)]
    else:
        mid = (y1 + y2) / 2
        verts = [(x1,y1,eave),(x2,y1,eave),(x1,mid,ridge),(x2,mid,ridge),(x1,y2,eave),(x2,y2,eave)]
        faces = [(0,1,3,2),(2,3,5,4)]
    return mesh(collection,name,verts,faces,parent,mat)


def gable_infill(collection, name, x1, x2, y, eave, ridge, parent, mat):
    return mesh(collection,name,[(x1,y,eave),((x1+x2)/2,y,ridge),(x2,y,eave)],[(0,1,2)],parent,mat)


def hip_roof(collection, name, x1, x2, y1, y2, eave, ridge, ridge_y1, ridge_y2, parent, mat):
    verts=[(x1,y1,eave),(x2,y1,eave),(x2,y2,eave),(x1,y2,eave),((x1+x2)/2,ridge_y1,ridge),((x1+x2)/2,ridge_y2,ridge)]
    return mesh(collection,name,verts,[(0,1,4),(1,2,5,4),(2,3,5),(3,0,4,5)],parent,mat)


def camera(collection, name, location_ft, target_ft, ortho=None):
    data=bpy.data.cameras.new(name); obj=bpy.data.objects.new(name,data); collection.objects.link(obj)
    obj.location=tuple(v*FT for v in location_ft)
    obj.rotation_euler=(Vector(tuple(v*FT for v in target_ft))-obj.location).to_track_quat("-Z","Y").to_euler()
    if ortho: data.type="ORTHO"; data.ortho_scale=ortho*FT
    return obj


def frame_opening(collection, name, start, end, bottom, top, floor, parent, wood, glass, kind="window"):
    a=Vector(start); b=Vector(end); direction=b-a; length=direction.length; direction.normalize()
    normal=Vector((-direction.y,direction.x)); depth=.16; trim=.14
    parts=[
        ("left",a-trim*direction,a+trim*direction,bottom,top),
        ("right",b-trim*direction,b+trim*direction,bottom,top),
        ("top",a,b,top-trim,top+trim),
    ]
    if kind=="window": parts.append(("bottom",a,b,bottom-trim,bottom+trim))
    for suffix,p,q,z1,z2 in parts:
        wall_piece(collection,f"{name}_{suffix}",p,q,floor+z1,floor+z2,depth,parent,wood)
    if kind=="window":
        center_a=a+normal*.01; center_b=b+normal*.01
        wall_piece(collection,f"{name}_glass",center_a,center_b,floor+bottom+.12,floor+top-.12,.035,parent,glass)
    else:
        leaf=wall_piece(collection,f"{name}_leaf",a,b,floor+bottom,floor+top,.10,parent,wood)
        leaf["pose"]="closed"
        leaf["source_dimensions_ft"]=(length,top-bottom)


def main_house_exterior(root, roofs, stucco, roof, wood, glass):
    node=empty(root,"site_main_house_exterior")
    node["source"]="A2.2, A3.0, A3.1, A0.5 and listing exterior photographs"
    # Frames and glazing use the accepted wall apertures; wall shells remain owned by HOUSE_LAYOUT.
    exterior={"g_west","g_rear","g_east_rear","g_bed3_south","g_foyer_left_outer","g_foyer_entry","g_foyer_right_outer",
              "u_west_rear","u_west_front","u_bed9_north","u_bath3_west","u_rear","u_library_east","u_rear_shoulder","u_east_rear","u_east_front","u_bed4_front","u_bed5_front"}
    for floor,walls in [(0,GROUND_WALLS),(10,UPPER_WALLS)]:
        for spec in walls:
            if spec["id"] not in exterior: continue
            start=Vector(spec["start"]); delta=Vector(spec["end"])-start; delta.normalize()
            for i,opening in enumerate(spec.get("apertures",())):
                a=start+delta*opening["start"]; b=start+delta*opening["end"]
                frame_opening(root,f"site_frame_{spec['id']}_{i}",a,b,opening.get("bottom",0),opening.get("top",7),floor,node,wood,glass,opening["kind"])
    # Contiguous A2.2 trace.  Ridge/hip/valley locations are proportional
    # traces; the 28ft2in ridge height follows A3.0's vertical chain.
    roof_vertices=[
      (-.9,-1.0,19.45), (14.1,-.1,19.45), (23.8,-1.0,24.4), (33.6,-1.0,19.45),
      (23.8,9.8,24.4), (16.5,17.0,28.17), (16.5,24.0,28.17),
      (-.9,40.5,19.45), (33.6,40.5,19.45),
    ]
    main_roof=mesh(roofs,"site_roof_main_complex",roof_vertices,[
      (0,1,5),(1,4,5), # front-left planes; edge 1-4 is the A2.2 valley
      (0,5,7),(5,6,7), # north main planes; edge 0-5 is the front hip
      (7,6,8),         # rear hip
      (6,5,8),(5,4,8),(4,3,8), # south main planes
      (1,2,4),         # north front-gable plane
      (2,3,4),         # south front-gable plane; edge 2-4 is its ridge
    ],node,roof)
    main_roof["traced_edges"]="ridge 5-6; front hip 0-5; valley 1-4; front gable ridge 2-4; rear hips 7-6 and 6-8"
    gable_infill(root,"site_main_front_gable_infill",14.1,33.6,-1.02,19.45,24.4,node,stucco)
    for label,a,b in [("front",(-.9,-1.0),(33.6,-1.0)),("rear",(-.9,40.5),(33.6,40.5)),("north",(-.9,-1.0),(-.9,40.5)),("south",(33.6,-1.0),(33.6,40.5))]:
        wall_piece(root,f"site_roof_fascia_{label}",a,b,18.5,19.45,.18,node,stucco)
    # The porch covers the exterior steps and recessed entry only.  Its rear
    # eave stops before the upper BED4 footprint shown on A2.0/A3.0.
    gable_roof(roofs,"site_roof_front_porch",-.8,16.2,-3.0,-.8,10.0,13.0,node,roof,True,.35)
    # Rear lower shed/lean-to roofs visible in A2.2/A3.1.
    rear_pitch=mesh(roofs,"site_roof_rear_pitch_break",[(-.9,40.5,19.45),(33.6,40.5,19.45),(31.8,50.1,18.65),(4.8,50.1,18.65)],[(0,1,2,3)],node,roof)
    rear_pitch["height_note"]="junction traced from A2.2; outer eave inferred above the 18ft6in upper ceiling from A3.0/A3.1"
    mesh(roofs,"site_roof_rear_lower_shed",[(-1.0,40.0,10.0),(7.0,40.0,10.0),(-1.0,51.2,9.1),(7.0,51.2,9.1)],[(0,1,3,2)],node,roof)
    # A2.2 marks two first-floor sheds below the upper south eave.  Their
    # longitudinal footprints are traced; undimensioned projection and pitch
    # are inferred from A3.0 and kept outside the upper wall outer face.
    for label,inner_x,y1,y2 in [("dining",32.68,15.0,27.8),("rear_south",30.82,39.8,49.5)]:
        surface=mesh(roofs,f"site_roof_south_{label}_shed",[
            (inner_x,y1,9.85),(inner_x,y2,9.85),(34.25,y1,9.35),(34.25,y2,9.35),
        ],[(0,1,3,2)],node,roof)
        surface["source"]="A2.2 footprint and A3.0 height relationship"
        surface["dimensions_note"]="lateral projection and pitch inferred"
        wall_piece(root,f"site_roof_south_{label}_fascia",(34.25,y1),(34.25,y2),9.15,9.35,.16,node,stucco)
    # The recessed porch meets the fixed FFL at zero.  Four inferred 1ft
    # treads descend toward a local grade 0.6ft below FFL as seen in photo 17.
    prism(root,"site_front_porch",[(2,-3),(14,-3),(14,3.35),(2,3.35)],-.15,0,node,stucco)
    for i in range(4):
        y2=-3-i; y1=y2-1; top=-(i+1)*.15
        prism(root,f"site_front_step_{i}",[(4-i*.5,y1),(12+i*.5,y1),(12+i*.5,y2),(4-i*.5,y2)],top-.15,top,node,stucco)
    rear_stairs(root,node,wood)


def rear_stairs(root, parent, wood):
    """Photo-supported rear deck stair: dimensions are inferred, arrangement is fixed."""
    node=empty(root,"site_rear_exterior_stair",parent); node["dimensions"]="inferred from listing photos 18-21"
    prism(root,"site_rear_upper_landing",[(26,49.5),(32,49.5),(32,54.5),(26,54.5)],9.75,10.0,node,wood)
    # Short flight moves away from the rear wall to the switchback landing.
    for i in range(4):
        y1=54.5+i*.75; y2=y1+.75; z=9.75-(i+1)*.45
        prism(root,f"site_rear_stair_upper_{i:02}",[(27,y1),(31,y1),(31,y2),(27,y2)],z-.15,z,node,wood)
    prism(root,"site_rear_switchback_landing",[(25,57.5),(31,57.5),(31,61.5),(25,61.5)],7.8,7.95,node,wood)
    # Photo 19 fixes the long flight parallel to the facade toward model -X.
    steps=13
    for i in range(steps):
        x2=25-i*22/steps; x1=25-(i+1)*22/steps; z=7.8-(i+1)*7.8/steps
        prism(root,f"site_rear_stair_lower_{i:02}",[(x1,57.5),(x2,57.5),(x2,61.5),(x1,61.5)],z-.15,z,node,wood)
    for y in (57.5,61.5): beam3d(root,f"site_rear_stair_lower_rail_{y}",(25,y,11.3),(3,y,3.5),.14,node,wood)
    for y in (58.0,61.0): beam3d(root,f"site_rear_stair_lower_stringer_{y}",(25,y,7.55),(3,y,.15),.28,node,wood)
    for x in (27,31): beam3d(root,f"site_rear_stair_upper_rail_{x}",(x,54.5,13.2),(x,57.5,11.3),.14,node,wood)
    for x in (27.4,30.6): beam3d(root,f"site_rear_stair_upper_stringer_{x}",(x,54.5,9.55),(x,57.5,7.9),.28,node,wood)
    for x in (26,32): wall_piece(root,f"site_rear_upper_guard_{x}",(x,49.5),(x,54.5),10,13.5,.12,node,wood)
    for label,x,y,height in [("upper_n",26,49.7,10),("upper_s",32,49.7,10),("switch_n",25.2,57.7,7.8),("switch_s",30.8,61.3,7.8)]:
        beam3d(root,f"site_rear_stair_post_{label}",(x,y,0),(x,y,height),.28,node,wood)


def detached(root, roofs, stucco, roof, wood, glass):
    node=empty(root,"site_detached_unit")
    node["source"]="A1.0 and supplemental A2.3 dated 2023-04-03"
    node["rotation_note"]="12ft dimension follows parcel; 17ft11in dimension runs across parcel; entry faces south"
    floor=[(DETACHED_WEST_X,DETACHED_FRONT_Y),(DETACHED_EAST_X,DETACHED_FRONT_Y),(DETACHED_EAST_X,DETACHED_REAR_Y),(DETACHED_WEST_X,DETACHED_REAR_Y)]
    prism(root,"site_detached_floor",floor,-.08,0,node,wood)
    h=5/24
    wall_floor=[(DETACHED_WEST_X+h,DETACHED_FRONT_Y+h),(DETACHED_EAST_X-h,DETACHED_FRONT_Y+h),(DETACHED_EAST_X-h,DETACHED_REAR_Y-h),(DETACHED_WEST_X+h,DETACHED_REAR_Y-h)]
    specs=[
      {"id":"site_detached_west_gable","start":wall_floor[0],"end":wall_floor[1],"apertures":[{"kind":"window","start":2.5,"end":5,"bottom":2+8/12,"top":6+4/12,"source_mark":"300.2"},{"kind":"window","start":12,"end":15,"bottom":2+8/12,"top":6+4/12,"source_mark":"300.1"}]},
      {"id":"site_detached_south_entry","start":wall_floor[1],"end":wall_floor[2],"apertures":[{"kind":"door","start":6+2/12,"end":9+2/12,"bottom":0,"top":6+8/12,"source_mark":"door 300.1"}]},
      {"id":"site_detached_east_gable","start":wall_floor[2],"end":wall_floor[3],"apertures":[{"kind":"window","start":2.5,"end":5.5,"bottom":3+4/12,"top":6+4/12,"source_mark":"300.3"},{"kind":"window","start":14.5,"end":15.5,"bottom":4+8/12,"top":6+4/12,"source_mark":"300.4"}]},
      {"id":"site_detached_north","start":wall_floor[3],"end":wall_floor[0],"apertures":[{"kind":"window","start":8,"end":11,"bottom":4+2/12,"top":7+2/12,"source_mark":"300.5"}]},
    ]
    for spec in specs:
        wall_with_apertures(root,spec,0,8+0.5/12,node,stucco,5/12)
        start=Vector(spec["start"]); d=Vector(spec["end"])-start; d.normalize()
        for i,a in enumerate(spec["apertures"]): frame_opening(root,f"{spec['id']}_frame_{i}",start+d*a["start"],start+d*a["end"],a["bottom"],a["top"],0,node,wood,glass,a["kind"])
    # A2.3 washroom is an L in the north/east corner after site rotation.
    bath_south_x=DETACHED_WEST_X+5/12+6+8/12+5/24
    bath_west_y=DETACHED_FRONT_Y+5/12+4+8/12+5/24
    wall_with_apertures(root,{"id":"site_detached_bath_south","start":(bath_south_x,bath_west_y),"end":(bath_south_x,DETACHED_REAR_Y-5/12),"apertures":[]},0,8+0.5/12,node,stucco,5/12)
    wall_with_apertures(root,{"id":"site_detached_bath_west","start":(DETACHED_WEST_X+5/12,bath_west_y),"end":(bath_south_x,bath_west_y),"apertures":[{"kind":"door","start":3+10/12,"end":6+6/12,"bottom":0,"top":6+8/12}]},0,8+0.5/12,node,stucco,5/12)
    gable_roof(roofs,"site_detached_roof",DETACHED_WEST_X,DETACHED_EAST_X,DETACHED_FRONT_Y,DETACHED_REAR_Y,8+0.5/12,12+1/12,node,roof,True)
    gable_infill(root,"site_detached_gable_west",DETACHED_WEST_X,DETACHED_EAST_X,DETACHED_FRONT_Y-.01,8+0.5/12,12+1/12,node,stucco)
    gable_infill(root,"site_detached_gable_east",DETACHED_WEST_X,DETACHED_EAST_X,DETACHED_REAR_Y+.01,8+0.5/12,12+1/12,node,stucco)


def garage(root, roofs, siding, roof, wood):
    node=empty(root,"site_garage"); node["source"]="A1.0 footprint and listing photo 22"; node["height"]="inferred from photo"
    outline=[(GARAGE_WEST_X,GARAGE_FRONT_Y),(GARAGE_EAST_X,GARAGE_FRONT_Y),(GARAGE_EAST_X,GARAGE_REAR_Y),(GARAGE_WEST_X,GARAGE_REAR_Y)]
    prism(root,"site_garage_slab",outline,-.1,0,node,siding)
    h=.35/2
    wall_outline=[(GARAGE_WEST_X+h,GARAGE_FRONT_Y+h),(GARAGE_EAST_X-h,GARAGE_FRONT_Y+h),(GARAGE_EAST_X-h,GARAGE_REAR_Y-h),(GARAGE_WEST_X+h,GARAGE_REAR_Y-h)]
    for i,(a,b) in enumerate(zip(wall_outline,wall_outline[1:]+wall_outline[:1])): wall_piece(root,f"site_garage_wall_{i}",a,b,0,8,.35,node,siding)
    wall_piece(root,"site_garage_double_door",(GARAGE_WEST_X,GARAGE_FRONT_Y-.19),(GARAGE_EAST_X,GARAGE_FRONT_Y-.19),0,7,.12,node,wood)
    gable_roof(roofs,"site_garage_roof",GARAGE_WEST_X,GARAGE_EAST_X,GARAGE_FRONT_Y,GARAGE_REAR_Y,8.2,10.8,node,roof,True)
    gable_infill(root,"site_garage_gable_front",GARAGE_WEST_X,GARAGE_EAST_X,GARAGE_FRONT_Y-.01,8.0,10.8,node,siding)
    gable_infill(root,"site_garage_gable_rear",GARAGE_WEST_X,GARAGE_EAST_X,GARAGE_REAR_Y+.01,8.0,10.8,node,siding)


def site_surfaces(root, ground, concrete, landscape):
    node=empty(root,"site_parcel")
    # The inferred front yard is 0.6ft below FFL, with side slopes rising
    # beside the four entry treads to the retained rear grade.
    x1,x2=PROPERTY_WEST_X,PROPERTY_EAST_X; y1,y2=PROPERTY_FRONT_Y,PROPERTY_REAR_Y
    vertices=[
        (x1,y1,-.62),(x2,y1,-.62),(x2,-7,-.62),(x1,-7,-.62),
        (x1,-3,-.16),(x2,-3,-.16),(x2,y2,-.16),(x1,y2,-.16),
        (x1,-7,-.62),(1,-7,-.62),(1,-3,-.16),(x1,-3,-.16),
        (15,-7,-.62),(x2,-7,-.62),(x2,-3,-.16),(15,-3,-.16),
    ]
    faces=[(0,1,2,3),(4,5,6,7),(8,9,10,11),(12,13,14,15)]
    mesh(root,"site_ground",vertices,faces,node,ground)
    # A1.0-supported circulation and parking zones at diagrammatic detail.
    prism(root,"site_front_walk",[(11,PROPERTY_FRONT_Y),(16,PROPERTY_FRONT_Y),(16,-7),(11,-7)],-.7,-.6,node,concrete)
    prism(root,"site_north_side_walk",[(-3,0),(0,0),(0,73),(-3,73)],-.15,-.05,node,concrete)
    # A1.0 shows a continuous 10ft south passage and concrete connections
    # around planted courtyard islands rather than a single paved courtyard.
    prism(root,"site_south_passage",[(35,0),(45,0),(45,91.5),(35,91.5)],-.15,-.05,node,concrete)
    prism(root,"site_courtyard_cross_walk",[(0,50),(35,50),(35,55),(0,55)],-.15,-.05,node,concrete)
    prism(root,"site_courtyard_north_walk",[(0,73),(35,73),(35,78),(0,78)],-.15,-.05,node,concrete)
    prism(root,"site_courtyard_center_walk",[(15,55),(20,55),(20,73),(15,73)],-.15,-.05,node,concrete)
    prism(root,"site_detached_entry_walk",[(DETACHED_EAST_X,86.5),(35,86.5),(35,91.5),(DETACHED_EAST_X,91.5)],-.15,-.05,node,concrete)
    prism(root,"site_detached_walk",[(DETACHED_WEST_X-2,DETACHED_FRONT_Y-5),(DETACHED_EAST_X+2,DETACHED_FRONT_Y-5),(DETACHED_EAST_X+2,DETACHED_REAR_Y+6),(DETACHED_WEST_X-2,DETACHED_REAR_Y+6)],-.14,-.06,node,concrete)
    prism(root,"site_rear_access",[(PROPERTY_WEST_X,GARAGE_FRONT_Y-5),(PROPERTY_EAST_X,GARAGE_FRONT_Y-5),(PROPERTY_EAST_X,PROPERTY_REAR_Y),(PROPERTY_WEST_X,PROPERTY_REAR_Y)],-.14,-.05,node,concrete)
    prism(root,"site_rear_yard_walk",[(19,99.5),(24,99.5),(24,GARAGE_FRONT_Y-5),(19,GARAGE_FRONT_Y-5)],-.15,-.05,node,concrete)
    for i in range(3):
        x1=13+i*8.1
        stall=prism(root,f"site_parking_stall_{i+1}",[(x1,GARAGE_FRONT_Y),(x1+8.1,GARAGE_FRONT_Y),(x1+8.1,GARAGE_REAR_Y),(x1,GARAGE_REAR_Y)],-.13,-.035,node,concrete)
        stall["dimensions"]="8ft1in source width; alongside garage over its source footprint depth"
    for i,(x1,x2,y1,y2,bottom,top) in enumerate([
        (-4,1,-20,-7,-.7,-.6),(17,35,-20,-7,-.7,-.6),
        (-4,1,-3,0,-.14,-.04),(17,35,-3,45,-.14,-.04),
        (2,15,55,73,-.14,-.04),(20,33,55,73,-.14,-.04),
        (20,35,78,86.5,-.14,-.04),(24,35,91.5,128,-.14,-.04),(1,18,99.5,128,-.14,-.04),
        (-4,-2,73,145,-.14,-.04),
    ]):
        prism(root,f"site_landscape_zone_{i}",[(x1,y1),(x2,y1),(x2,y2),(x1,y2)],bottom,top,node,landscape)


def main():
    if not bpy.data.filepath: raise RuntimeError("Load the Sage master before applying the site updater")
    if not bpy.data.collections.get("HOUSE_LAYOUT"): raise RuntimeError("HOUSE_LAYOUT is required")
    root=owned_collection(OWNED); roofs=owned_collection(ROOFS,root)
    authoring=bpy.data.collections.get("AUTHORING") or bpy.context.scene.collection
    cams=owned_collection(CAMERAS,authoring)
    stucco=material("site_stucco",(.72,.70,.65)); roof=material("site_roof",(.14,.16,.17)); wood=material("site_wood",(.34,.12,.06)); glass=material("site_glass",(.18,.38,.48),.2)
    glass.metallic=.05; ground=material("site_ground",(.20,.28,.13)); concrete=material("site_concrete",(.42,.43,.40)); landscape=material("site_landscape",(.14,.31,.10)); siding=material("site_garage_siding",(.52,.55,.54))
    site_surfaces(root,ground,concrete,landscape); main_house_exterior(root,roofs,stucco,roof,wood,glass); detached(root,roofs,stucco,roof,wood,glass); garage(root,roofs,siding,roof,wood)
    camera(cams,"site_plan",(20,68,245),(20,68,0),210)
    camera(cams,"site_perspective_front",(-72,-80,62),(17,38,8))
    camera(cams,"site_perspective_rear",(92,210,72),(20,105,7))
    camera(cams,"site_main_front",(16,-70,22),(16,8,12))
    camera(cams,"site_main_rear",(64,94,25),(17,45,10))
    camera(cams,"site_main_roof_plan",(16,29,85),(16,29,18),74)
    camera(cams,"site_detached_plan",((DETACHED_WEST_X+DETACHED_EAST_X)/2,(DETACHED_FRONT_Y+DETACHED_REAR_Y)/2,45),((DETACHED_WEST_X+DETACHED_EAST_X)/2,(DETACHED_FRONT_Y+DETACHED_REAR_Y)/2,0),25)
    bpy.context.scene["site_layout_source"]="A1.0, A2.2, A3.0/A3.1, A0.5, supplemental A2.3, photos 18-22"
    bpy.context.scene["site_layout_ownership"]="SITE_LAYOUT, SITE_ROOFS and SITE_LAYOUT_CAMERAS"
    bpy.context.scene["site_layout_revision"]=1
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    print(f"Updated full site in {bpy.data.filepath}")


if __name__=="__main__":
    try: main()
    except Exception as exc: print(f"ERROR: {exc}",file=sys.stderr); raise
