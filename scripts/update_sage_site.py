"""Replace the separately owned full-site architecture in the loaded Sage master."""

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sage_house_builder import empty, owned_collection, prism, wall_piece, wall_with_apertures
from sage_house_layout import GROUND_WALLS, UPPER_WALLS
from sage_scene import DINING_DEPTH, DINING_RIGHT_STEP, FRONT_WALL, LIVING_DEPTH, LIVING_WIDTH, LIVING_X, SHARED_WALL, FT
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


def profile_y(collection, name, points_xz, y1, y2, parent, mat):
    """Extrude a simple X/Z profile through a shallow Y depth."""
    count=len(points_xz)
    vertices=[(x,y1,z) for x,z in points_xz]+[(x,y2,z) for x,z in points_xz]
    faces=[tuple(range(count)),tuple(range(count,2*count))]
    for index in range(count):
        next_index=(index+1)%count
        faces.append((index,next_index,count+next_index,count+index))
    return mesh(collection,name,vertices,faces,parent,mat)


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


def vertical_disc(collection, name, center, radius, axis, parent, mat, segments=20):
    """Create a shallow vertical polygon for a photo-supported gable vent."""
    cx,cy,cz=center
    vertices=[center]
    for index in range(segments):
        angle=math.pi/2+2*math.pi*index/segments
        if axis=="y": vertices.append((cx+math.cos(angle)*radius,cy,cz+math.sin(angle)*radius))
        else: vertices.append((cx,cy+math.cos(angle)*radius,cz+math.sin(angle)*radius))
    faces=[tuple(range(1,segments+1))]
    return mesh(collection,name,vertices,faces,parent,mat)


def exterior_skin(collection, name, spec, elevation, height, inward, parent, mat):
    """Add a thin aperture-matched finish outside a canonical wall."""
    shift=-Vector(inward)*.20
    skin={**spec,"id":name,"start":tuple(Vector(spec["start"])+shift),"end":tuple(Vector(spec["end"])+shift),"thickness":.08}
    return wall_with_apertures(collection,skin,elevation,height,parent,mat,.08)


def gable_roof_finish(collection, name, x1, x2, y1, y2, eave, ridge, parent, roof, soffit, fascia, overhang=.7):
    """Build a gable roof with a visible underside and finished perimeter."""
    top=gable_roof(collection,name,x1,x2,y1,y2,eave,ridge,parent,roof,True,overhang)
    gable_roof(collection,f"{name}_soffit",x1,x2,y1,y2,eave-.16,ridge-.16,parent,soffit,True,overhang)
    mid=(x1+x2)/2
    for label,a,b in [
        ("eave_west",(x1-overhang,y1-overhang,eave-.08),(x1-overhang,y2+overhang,eave-.08)),
        ("eave_east",(x2+overhang,y1-overhang,eave-.08),(x2+overhang,y2+overhang,eave-.08)),
        ("rake_front_left",(x1-overhang,y1-overhang,eave-.08),(mid,y1-overhang,ridge-.08)),
        ("rake_front_right",(mid,y1-overhang,ridge-.08),(x2+overhang,y1-overhang,eave-.08)),
        ("rake_rear_left",(x1-overhang,y2+overhang,eave-.08),(mid,y2+overhang,ridge-.08)),
        ("rake_rear_right",(mid,y2+overhang,ridge-.08),(x2+overhang,y2+overhang,eave-.08)),
    ]: beam3d(collection,f"{name}_{label}",a,b,.20,parent,fascia)
    return top


def hip_roof(collection, name, x1, x2, y1, y2, eave, ridge, ridge_y1, ridge_y2, parent, mat):
    verts=[(x1,y1,eave),(x2,y1,eave),(x2,y2,eave),(x1,y2,eave),((x1+x2)/2,ridge_y1,ridge),((x1+x2)/2,ridge_y2,ridge)]
    return mesh(collection,name,verts,[(0,1,4),(1,2,5,4),(2,3,5),(3,0,4,5)],parent,mat)


def camera(collection, name, location_ft, target_ft, ortho=None, lens=50, shift_y=0, shift_x=0, rotation=None):
    data=bpy.data.cameras.new(name); obj=bpy.data.objects.new(name,data); collection.objects.link(obj)
    obj.location=tuple(v*FT for v in location_ft)
    obj.rotation_euler=rotation if rotation is not None else (Vector(tuple(v*FT for v in target_ft))-obj.location).to_track_quat("-Z","Y").to_euler()
    data.lens=lens
    data.shift_x=shift_x
    data.shift_y=shift_y
    if ortho: data.type="ORTHO"; data.ortho_scale=ortho*FT
    return obj


def frame_opening(collection, name, start, end, bottom, top, floor, parent, wood, glass, kind="window", depth=.16, recess=.01, reveals=False, inward=None, casing_offset=0, leaf_material=None):
    a=Vector(start); b=Vector(end); direction=b-a; length=direction.length; direction.normalize()
    normal=Vector((-direction.y,direction.x)); trim=.14
    inward=Vector(inward) if inward is not None else normal
    casing_shift=-inward*casing_offset
    parts=[
        ("left",a-trim*direction+casing_shift,a+trim*direction+casing_shift,bottom,top),
        ("right",b-trim*direction+casing_shift,b+trim*direction+casing_shift,bottom,top),
        ("top",a+casing_shift,b+casing_shift,top-trim,top+trim),
    ]
    if kind=="window": parts.append(("bottom",a+casing_shift,b+casing_shift,bottom-trim,bottom+trim))
    for suffix,p,q,z1,z2 in parts:
        wall_piece(collection,f"{name}_{suffix}",p,q,floor+z1,floor+z2,depth,parent,wood)
    if kind=="window":
        if reveals:
            for suffix,point in (("left",a),("right",b)):
                wall_piece(collection,f"{name}_{suffix}_reveal",point-inward*(casing_offset+depth/2),point+inward*recess,floor+bottom,floor+top,.07,parent,wood)
        center_a=a+inward*recess; center_b=b+inward*recess
        wall_piece(collection,f"{name}_glass",center_a,center_b,floor+bottom+.12,floor+top-.12,.035,parent,glass)
    else:
        leaf=wall_piece(collection,f"{name}_leaf",a,b,floor+bottom,floor+top,.10,parent,leaf_material or wood)
        leaf["pose"]="closed"
        leaf["source_dimensions_ft"]=(length,top-bottom)


def opening_bars(collection, name, start, end, bottom, top, floor, parent, material_value, columns=1, rows=1, depth=.10):
    a=Vector(start); b=Vector(end); direction=b-a; length=direction.length; direction.normalize()
    for index in range(1,columns):
        point=a+direction*(length*index/columns)
        wall_piece(collection,f"{name}_mullion_{index}",point-direction*.035,point+direction*.035,floor+bottom,floor+top,depth,parent,material_value)
    for index in range(1,rows):
        z=floor+bottom+(top-bottom)*index/rows
        wall_piece(collection,f"{name}_rail_{index}",a,b,z-.045,z+.045,depth,parent,material_value)


def side_sash_bars(collection, name, start, end, bottom, top, floor, parent, material_value):
    """Divide a wide center pane from two narrower, horizontally divided sashes."""
    a=Vector(start); b=Vector(end); direction=(b-a).normalized(); length=(b-a).length
    left=a+direction*length*.2; right=a+direction*length*.8
    for index,point in enumerate((left,right)):
        wall_piece(collection,f"{name}_mullion_{index}",point-direction*.035,point+direction*.035,floor+bottom,floor+top,.10,parent,material_value)
    z=floor+(bottom+top)/2
    wall_piece(collection,f"{name}_side_rail_left",a,left,z-.045,z+.045,.10,parent,material_value)
    wall_piece(collection,f"{name}_side_rail_right",right,b,z-.045,z+.045,.10,parent,material_value)


def open_guard(collection, name, a, b, bottom, parent, wood, rails=(.45,1.35,2.25,3.2), posts=5):
    a=Vector(a); b=Vector(b); direction=b-a; length=direction.length; direction.normalize()
    for index,height in enumerate(rails):
        wall_piece(collection,f"{name}_rail_{index}",a,b,bottom+height-.12,bottom+height+.12,.18,parent,wood)
    for index in range(posts+1):
        point=a+direction*(length*index/posts)
        wall_piece(collection,f"{name}_post_{index}",point-direction*.12,point+direction*.12,bottom,bottom+3.5,.28,parent,wood)


def front_details(root, roofs, node, stucco, soffit, terracotta, metal):
    # The porch mass follows the accepted entry footprint; these pieces express
    # its photographed gable edge, ridge cap, rounded header ends and stair rails.
    roof=gable_roof(roofs,"site_roof_front_porch",-.8,16.2,-3.0,-.8,9.0,12.3,node,terracotta,True,.35)
    roof["source"]="A2.2 footprint; front photos 14 and 17 material and edge character"
    gable_infill(root,"site_front_porch_gable",-.8,16.2,-3.36,9.0,12.3,node,stucco)
    beam3d(root,"site_front_porch_ridge",(7.7,-3.35,12.34),(7.7,-.45,12.34),.18,node,terracotta)
    beam3d(root,"site_front_porch_rake_left",(-1.15,-3.35,9),(7.7,-3.35,12.3),.18,node,terracotta)
    beam3d(root,"site_front_porch_rake_right",(7.7,-3.35,12.3),(16.55,-3.35,9),.18,node,terracotta)
    gable_roof(roofs,"site_roof_front_porch_soffit",-.8,16.2,-3.0,-.8,8.92,12.22,node,soffit,True,.35)
    for side,x1,x2 in (("left",2.0,3.6),("right",12.4,14.0)):
        prism(root,f"site_front_porch_pier_{side}",[(x1,-3.25),(x2,-3.25),(x2,-2.45),(x1,-2.45)],-2.75,6.7,node,stucco)
        prism(root,f"site_front_porch_rear_return_{side}",[(x1,2.65),(x2,2.65),(x2,3.35),(x1,3.35)],0,6.7,node,stucco)
    for side,center_x,start_angle,end_angle in [("left",4.85,math.pi/2,math.pi),("right",11.15,0,math.pi/2)]:
        curve=[]
        for index in range(7):
            angle=start_angle+(end_angle-start_angle)*index/6
            curve.append((center_x+1.25*math.cos(angle),6.7+1.25*math.sin(angle)))
        if side=="left":
            profile=[(2.0,6.7),(2.0,7.95),*curve]
        else:
            profile=[(11.15,7.95),(14.0,7.95),(14.0,6.7),*curve]
        profile_y(root,f"site_front_porch_curve_{side}",profile,-3.25,3.35,node,stucco)
    prism(root,"site_front_porch_header",[(2,-3.25),(14,-3.25),(14,3.35),(2,3.35)],7.95,8.95,node,stucco)
    prism(root,"site_front_porch_soffit",[(2,-3.25),(14,-3.25),(14,3.35),(2,3.35)],8.83,8.95,node,soffit)
    for side,x in [("left",4.0),("right",12.0)]:
        beam3d(root,f"site_front_stair_rail_top_{side}",(x,-3.0,3.05),(x,-8.0,.30),.14,node,metal)
        for index in range(6):
            y=-3.0-index
            tread=-min(index,5)*.55
            z=3.05-index*.55
            beam3d(root,f"site_front_stair_rail_post_{side}_{index}",(x,y,tread),(x,y,z),.12,node,metal)
    # Shallow slats make the small gable vent legible without changing the gable shell.
    for index,width in enumerate((1.0,1.25,1.45,1.25,1.0)):
        z=21.0+index*.22
        wall_piece(root,f"site_front_gable_vent_{index}",(23.8-width/2,-1.13),(23.8+width/2,-1.13),z,z+.09,.08,node,metal)


def screen_door(collection, name, start, end, bottom, top, floor, parent, metal, glass):
    a=Vector(start); b=Vector(end); direction=b-a; direction.normalize(); trim=.14
    for suffix,p,q,z1,z2 in [
        ("left",a-trim*direction,a+trim*direction,bottom,top),
        ("right",b-trim*direction,b+trim*direction,bottom,top),
        ("top",a,b,top-trim,top+trim),
    ]:
        wall_piece(collection,f"{name}_{suffix}",p,q,floor+z1,floor+z2,.16,parent,metal)
    leaf=wall_piece(collection,f"{name}_leaf",a,b,floor+bottom,floor+top,.035,parent,glass)
    leaf["pose"]="closed"
    leaf["source_dimensions_ft"]=((Vector(end)-Vector(start)).length,top-bottom)
    opening_bars(collection,name,start,end,bottom+.25,top-.25,floor,parent,metal,columns=4,rows=2,depth=.08)


def main_house_exterior(root, roofs, stucco, roof, soffit, trim, glass, terracotta, deck_wood, metal, concrete, utility_door):
    node=empty(root,"site_main_house_exterior")
    node["source"]="A2.2, A3.0, A3.1, A0.5 and listing exterior photographs"
    # Frames and glazing use the accepted wall apertures; wall shells remain owned by HOUSE_LAYOUT.
    exterior={"g_west","g_rear","g_east_rear","g_bed3_south","g_foyer_left_outer","g_foyer_entry","g_foyer_right_outer",
              "u_west_rear","u_west_front","u_bed9_north","u_bath3_west","u_rear","u_library_east","u_rear_shoulder","u_east_rear","u_east_front","u_bed4_front","u_bed5_front"}
    inward_by_wall={
        "g_west":(1,0),"u_west_rear":(1,0),"u_west_front":(1,0),"u_bath3_west":(1,0),
        "g_rear":(0,-1),"u_rear":(0,-1),"u_bed9_north":(0,-1),
        "g_east_rear":(-1,0),"u_library_east":(-1,0),"u_east_rear":(-1,0),"u_east_front":(-1,0),
        "g_foyer_left_outer":(0,1),"g_foyer_entry":(0,1),"g_foyer_right_outer":(0,1),"u_bed4_front":(0,1),"u_bed5_front":(0,1),
        "g_bed3_south":(0,-1),"u_rear_shoulder":(0,-1),
    }
    side_skin_walls={"g_west","g_east_rear","u_west_rear","u_west_front","u_bath3_west","u_library_east","u_east_rear","u_east_front"}
    for floor,walls in [(0,GROUND_WALLS),(10,UPPER_WALLS)]:
        for spec in walls:
            if spec["id"] not in exterior: continue
            if spec["id"] in side_skin_walls:
                exterior_skin(root,f"site_skin_{spec['id']}",spec,floor,9 if floor==0 else 8.5,inward_by_wall[spec["id"]],node,stucco)
                if floor==0:
                    base={**spec,"id":f"site_base_{spec['id']}","apertures":[]}
                    exterior_skin(root,base["id"],base,SITE_GRADE,-SITE_GRADE,inward_by_wall[spec["id"]],node,stucco)
            elif floor==0:
                base={**spec,"id":f"site_base_{spec['id']}","apertures":[]}
                if spec["id"]=="g_rear":
                    base["apertures"]=[{"kind":"door","start":.10,"end":4.02,"bottom":0,"top":-SITE_GRADE}]
                exterior_skin(root,base["id"],base,SITE_GRADE,-SITE_GRADE,inward_by_wall[spec["id"]],node,stucco)
            start=Vector(spec["start"]); delta=Vector(spec["end"])-start; delta.normalize()
            for i,opening in enumerate(spec.get("apertures",())):
                a=start+delta*opening["start"]; b=start+delta*opening["end"]
                name=f"site_frame_{spec['id']}_{i}"
                if opening["kind"]=="door":
                    screen_door(root,name,a,b,opening.get("bottom",0),opening.get("top",7),floor,node,metal,glass)
                else:
                    frame_opening(root,name,a,b,opening.get("bottom",0),opening.get("top",7),floor,node,trim,glass,opening["kind"],depth=.36,recess=.18,reveals=True,inward=inward_by_wall[spec["id"]],casing_offset=.08)
                    columns=1
                    if spec["id"]=="g_rear" and i==3: columns=2
                    rows=4 if spec["id"]=="u_bed5_front" and i==0 else 2
                    if spec["id"]=="u_bed5_front" and i==0: columns=4
                    bottom=opening.get("bottom",0)+.12; top=opening.get("top",7)-.12
                    sash_shift=Vector(inward_by_wall[spec["id"]])*.22
                    sash_a=a-sash_shift; sash_b=b-sash_shift
                    if spec["id"]=="u_bed5_front" and i==1:
                        side_sash_bars(root,name,sash_a,sash_b,bottom,top,floor,node,trim)
                    else:
                        opening_bars(root,name,sash_a,sash_b,bottom,top,floor,node,trim,columns,rows)
    # The detailed living/dining walls replace this portion of HOUSE_LAYOUT.
    # Cover their outward wallpaper/oak with site-owned finish and trim without
    # touching the protected detailed-room objects.
    living_x=(LIVING_X+LIVING_WIDTH)/FT
    living_y1=FRONT_WALL/FT; living_y2=(FRONT_WALL+LIVING_DEPTH)/FT
    living_center=(FRONT_WALL+2.52)/FT; living_width=4.5
    dining_x=(LIVING_X+LIVING_WIDTH+DINING_RIGHT_STEP)/FT
    dining_y1=(FRONT_WALL+LIVING_DEPTH+SHARED_WALL)/FT; dining_y2=dining_y1+DINING_DEPTH/FT
    detailed_sides=[
        ("living",living_x, living_y1,living_y2,[(living_center-living_width/2,living_center+living_width/2)]),
        ("dining",dining_x,dining_y1,dining_y2,[
            (dining_y1+1.345/FT-(3+4/12)/2,dining_y1+1.345/FT+(3+4/12)/2),
            (dining_y1+2.465/FT-(3+4/12)/2,dining_y1+2.465/FT+(3+4/12)/2),
        ]),
    ]
    for label,x,y1,y2,openings in detailed_sides:
        skin_y1=y1-.20 if label=="dining" else -.10
        skin_y2=y2+.20 if label=="dining" else y2
        spec={"id":f"site_skin_detail_{label}","start":(x,skin_y1),"end":(x,skin_y2),"apertures":[
            {"kind":"window","start":a-skin_y1,"end":b-skin_y1,"bottom":.76/FT,"top":(.76+1.58)/FT} for a,b in openings
        ]}
        exterior_skin(root,spec["id"],spec,0,9.08,(-1,0),node,stucco)
        base={**spec,"id":f"site_base_detail_{label}","apertures":[]}
        if label=="living":
            base["end"]=(x,dining_y1-.20)
        exterior_skin(root,base["id"],base,SITE_GRADE,-SITE_GRADE,(-1,0),node,stucco)
        start=Vector(spec["start"]); direction=Vector((0,1))
        for index,opening in enumerate(spec["apertures"]):
            a=start+direction*opening["start"]; b=start+direction*opening["end"]
            frame_opening(root,f"site_frame_detail_{label}_{index}",a,b,opening["bottom"],opening["top"],0,node,trim,glass,depth=.30,recess=-.12,reveals=True,inward=(-1,0),casing_offset=.28)
            opening_bars(root,f"site_frame_detail_{label}_{index}",a+Vector((.22,0)),b+Vector((.22,0)),opening["bottom"]+.12,opening["top"]-.12,0,node,trim,1,2)
    wall_piece(root,"site_skin_detail_dining_front_return",(living_x+.16,dining_y1-.20),(dining_x+.16,dining_y1-.20),0,9.08,.08,node,stucco)
    wall_piece(root,"site_skin_detail_dining_rear_return",(32.68+.16,dining_y2+.20),(dining_x+.16,dining_y2+.20),0,9.08,.08,node,stucco)
    wall_piece(root,"site_base_detail_dining_front_return",(living_x+.16,dining_y1-.20),(dining_x+.16,dining_y1-.20),SITE_GRADE,0,.08,node,stucco)
    wall_piece(root,"site_base_detail_dining_rear_return",(32.68+.16,dining_y2+.20),(dining_x+.16,dining_y2+.20),SITE_GRADE,0,.08,node,stucco)
    # The detailed living window remains in EXPORT; add an exterior-only trim
    # layer without touching its interior oak geometry or material.
    living_a=Vector((19.625,-.16)); living_b=Vector((28.625,-.16)); living_trim=.14
    living_direction=(living_b-living_a).normalized()
    for suffix,a,b,z1,z2 in [
        ("left",living_a-living_direction*living_trim,living_a+living_direction*living_trim,2.493,7.677),
        ("right",living_b-living_direction*living_trim,living_b+living_direction*living_trim,2.493,7.677),
        ("bottom",living_a,living_b,2.353,2.633),
        ("top",living_a,living_b,7.537,7.817),
    ]:
        wall_piece(root,f"site_frame_living_front_{suffix}",a,b,z1,z2,.16,node,trim)
    living_width=(living_b-living_a).length
    for index,fraction in enumerate((.19,.81)):
        point=living_a+living_direction*living_width*fraction
        wall_piece(root,f"site_frame_living_front_mullion_{index}",point-living_direction*.035,point+living_direction*.035,2.613,7.557,.10,node,trim)
    living_mid=(2.613+7.557)/2
    left_mullion=living_a+living_direction*living_width*.19
    right_mullion=living_a+living_direction*living_width*.81
    wall_piece(root,"site_frame_living_front_side_rail_left",living_a,left_mullion,living_mid-.045,living_mid+.045,.10,node,trim)
    wall_piece(root,"site_frame_living_front_side_rail_right",right_mullion,living_b,living_mid-.045,living_mid+.045,.10,node,trim)
    wall_piece(root,"site_frame_living_front_exterior_glass",(19.625,-.12),(28.625,-.12),2.613,7.557,.035,node,glass)
    # Site-owned exterior skin hides the detailed room's interior wallpaper
    # without changing its protected wall, window, or material payload.
    for suffix,a,b,z1,z2 in [
        ("left",(14,-.10),(19.625,-.10),0,9),
        ("right",(28.625,-.10),(32.68,-.10),0,9),
        ("below",(19.625,-.10),(28.625,-.10),0,2.353),
        ("above",(19.625,-.10),(28.625,-.10),7.557,9),
    ]:
        wall_piece(root,f"site_living_front_stucco_{suffix}",a,b,z1,z2,.10,node,stucco)
    wall_piece(root,"site_base_living_front",(14,-.10),(32.68,-.10),SITE_GRADE,0,.10,node,stucco)
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
    profile_y(root,"site_main_front_gable_infill",[(14.1,18.5),(14.1,19.45),(23.8,24.4),(33.6,19.45),(33.6,18.5)],-1.08,-.96,node,stucco)
    underside=[(x,y,z-.16) for x,y,z in roof_vertices]
    mesh(roofs,"site_roof_main_complex_soffit",underside,[
      (0,1,5),(1,4,5),(0,5,7),(5,6,7),(7,6,8),(6,5,8),(5,4,8),(4,3,8),(1,2,4),(2,3,4),
    ],node,soffit)
    prism(roofs,"site_roof_front_left_soffit",[(-.9,-1.0),(14.1,-1.0),(14.1,.05),(-.9,.05)],19.20,19.40,node,soffit)
    prism(roofs,"site_roof_rear_soffit",[(-.9,39.45),(33.6,39.45),(33.6,40.5),(-.9,40.5)],19.20,19.40,node,soffit)
    prism(roofs,"site_roof_north_soffit",[(-.9,-1.0),(.15,-1.0),(.15,40.5),(-.9,40.5)],19.20,19.40,node,soffit)
    prism(roofs,"site_roof_south_soffit",[(32.55,-1.0),(33.6,-1.0),(33.6,40.5),(32.55,40.5)],19.20,19.40,node,soffit)
    for label,a,b in [
        ("front",(.15,.05),(32.55,.05)),
        ("rear",(.15,39.45),(32.55,39.45)),
        ("north",(.15,.05),(.15,39.45)),
        ("south",(32.55,.05),(32.55,39.45)),
    ]:
        wall_piece(roofs,f"site_roof_frieze_{label}",a,b,18.5,19.22,.12,node,soffit)
    for label,a,b in [("front",(-.9,-1.0),(14.1,-1.0)),("rear",(-.9,40.5),(33.6,40.5)),("north",(-.9,-1.0),(-.9,40.5)),("south",(33.6,-1.0),(33.6,40.5))]:
        wall_piece(root,f"site_roof_fascia_{label}",a,b,18.5,19.45,.18,node,stucco)
    beam3d(root,"site_roof_front_gable_rake_left",(14.1,-1.1,19.45),(23.8,-1.1,24.4),.22,node,stucco)
    beam3d(root,"site_roof_front_gable_rake_right",(23.8,-1.1,24.4),(33.6,-1.1,19.45),.22,node,stucco)
    # The porch covers the exterior steps and recessed entry only.  Its rear
    # eave stops before the upper BED4 footprint shown on A2.0/A3.0.
    front_details(root,roofs,node,stucco,soffit,terracotta,metal)
    # Rear lower shed/lean-to roofs visible in A2.2/A3.1.
    rear_pitch=mesh(roofs,"site_roof_rear_pitch_break",[(-.9,40.5,19.45),(33.6,40.5,19.45),(31.8,50.1,18.65),(4.8,50.1,18.65)],[(0,1,2,3)],node,roof)
    rear_pitch["height_note"]="junction traced from A2.2; outer eave inferred above the 18ft6in upper ceiling from A3.0/A3.1"
    mesh(roofs,"site_roof_rear_pitch_north_closure",[(-.9,40.5,18.5),(-.9,40.5,19.45),(4.8,50.1,18.65),(4.8,50.1,18.5)],[(0,1,2,3)],node,soffit)
    mesh(roofs,"site_roof_rear_pitch_south_closure",[(33.6,40.5,18.5),(33.6,40.5,19.45),(31.8,50.1,18.65),(31.8,50.1,18.5)],[(0,1,2,3)],node,soffit)
    mesh(roofs,"site_roof_rear_pitch_inner_south_closure",[(30.82,40.5,18.5),(30.82,40.5,19.45),(30.82,50.1,18.65),(30.82,50.1,18.5)],[(0,1,2,3)],node,soffit)
    mesh(roofs,"site_roof_rear_lower_shed",[(-1.0,40.0,10.0),(7.0,40.0,10.0),(-1.0,51.2,9.1),(7.0,51.2,9.1)],[(0,1,3,2)],node,roof)
    for side,x in (("north",-1.0),("south",7.0)):
        mesh(roofs,f"site_roof_rear_lower_shed_{side}_closure",[(x,40,9),(x,40,10),(x,51.2,9.1),(x,51.2,9)],[(0,1,2,3)],node,soffit)
    # A2.2 marks two first-floor sheds below the upper south eave.  Their
    # longitudinal footprints are traced; undimensioned projection and pitch
    # are inferred from A3.0 and kept outside the upper wall outer face.
    for label,inner_x,y1,y2 in [("dining",32.68,15.0,27.8),("rear_south",30.82,39.8,49.5)]:
        surface=mesh(roofs,f"site_roof_south_{label}_shed",[
            (inner_x,y1,9.85),(inner_x,y2,9.85),(34.25,y1,9.35),(34.25,y2,9.35),
        ],[(0,1,3,2)],node,terracotta)
        surface["source"]="A2.2 footprint and A3.0 height relationship"
        surface["dimensions_note"]="lateral projection and pitch inferred"
        wall_piece(root,f"site_roof_south_{label}_fascia",(34.25,y1),(34.25,y2),9.15,9.35,.16,node,stucco)
        wall_piece(roofs,f"site_roof_south_{label}_inner_closure",(inner_x,y1),(inner_x,y2),9.0,9.85,.10,node,soffit)
        for end,y in (("front",y1),("rear",y2)):
            profile_y(roofs,f"site_roof_south_{label}_{end}_closure",[(inner_x,9),(inner_x,9.85),(34.25,9.35),(34.25,9)],y-.04,y+.04,node,soffit)
    # The recessed porch meets the fixed FFL at zero.  Four intermediate
    # treads form five inferred 6.6in rises to the photographed approach.
    prism(root,"site_front_porch",[(2,-3),(14,-3),(14,3.35),(2,3.35)],SITE_GRADE,0,node,stucco)
    wall_piece(root,"site_front_porch_slab_face",(2,-3.0),(14,-3.0),-.55,0,.24,node,stucco)
    for i in range(4):
        y2=-3-i; y1=y2-1; top=-(i+1)*.55
        prism(root,f"site_front_step_{i}",[(4-i*.5,y1),(12+i*.5,y1),(12+i*.5,y2),(4-i*.5,y2)],-2.75,top,node,stucco)
    prism(root,"site_front_approach",[(2,-8),(14,-8),(14,-7),(2,-7)],-2.93,-2.75,node,stucco)
    rear_patio(root,node,stucco,soffit,trim,metal,concrete,utility_door)
    rear_stairs(root,node,deck_wood)


def rear_patio(root, parent, stucco, soffit, trim, metal, concrete, utility_door):
    """Plan-traced raised rear patio; member sizes and heights are photo-estimated."""
    node=empty(root,"site_rear_patio",parent)
    node["source"]="current ground plan; pre-renovation rear photographs 18, 19 and 21"
    rear_y,outer_y=49.394,53.3
    prism(root,"site_rear_patio_base",[(4.5,rear_y),(19,rear_y),(19,outer_y),(4.5,outer_y)],SITE_GRADE,-.16,node,stucco)
    prism(root,"site_rear_patio_slab",[(4.5,rear_y),(19,rear_y),(19,outer_y),(4.5,outer_y)],-.16,0,node,concrete)
    prism(root,"site_rear_patio_canopy",[(0,rear_y),(19,rear_y),(19,outer_y),(0,outer_y)],8.65,8.9,node,soffit)
    for label,x1,x2 in (("north",4.5,5.2),("middle",11.15,11.85),("south",18.45,19)):
        prism(root,f"site_rear_patio_pier_{label}",[(x1,53.05),(x2,53.05),(x2,53.3),(x1,53.3)],0,7.9,node,stucco)
    wall_piece(root,"site_rear_patio_header",(4.5,53.175),(19,53.175),7.9,8.9,.25,node,stucco)
    for label,x,flip in (("north",5.2,1),("middle_n",11.15,-1),("middle_s",11.85,1),("south",18.45,-1)):
        points=[(x,7.9),(x,6.9)]
        for index in range(1,7):
            angle=index*math.pi/12
            points.append((x+flip*(1-math.cos(angle)),6.9+math.sin(angle)))
        profile_y(root,f"site_rear_patio_curve_{label}",points,53.05,53.3,node,stucco)
    wall_piece(root,"site_rear_patio_south_header",(18.875,rear_y),(18.875,outer_y),7.9,8.9,.25,node,stucco)
    for label,y,flip in (("rear",rear_y,1),("outer",outer_y,-1)):
        points=[(y,7.9),(y,6.9)]
        for index in range(1,7):
            angle=index*math.pi/12
            points.append((y+flip*(1-math.cos(angle)),6.9+math.sin(angle)))
        vertices=[(x,value_y,z) for x in (18.75,19) for value_y,z in points]
        count=len(points); faces=[tuple(range(count)),tuple(range(count,2*count))]
        faces.extend((i,(i+1)%count,count+(i+1)%count,count+i) for i in range(count))
        mesh(root,f"site_rear_patio_side_curve_{label}",vertices,faces,node,stucco)
    open_guard(root,"site_rear_patio_guard",(5.25,52.98),(17.9,52.98),0,node,metal,rails=(.45,1.4,2.35),posts=7)
    for index in range(4):
        x1=19+index; x2=x1+1; top=-(index+1)*.55
        prism(root,f"site_rear_patio_step_{index}",[(x1,50),(x2,50),(x2,53.3),(x1,53.3)],SITE_GRADE,top,node,concrete)
    for y in (50,53.3):
        beam3d(root,f"site_rear_patio_stair_rail_{y}",(19,y,3.2),(23,y,1.0),.14,node,metal)
        for index in range(5):
            x=19+index; tread=-min(index,5)*.55
            beam3d(root,f"site_rear_patio_stair_post_{y}_{index}",(x,y,tread),(x,y,tread+3.2),.12,node,metal)
    utility={"id":"site_rear_utility_outer","start":(0,53.3),"end":(4.5,53.3),"apertures":[
        {"kind":"door","start":1,"end":3.5,"bottom":0,"top":6+8/12},
    ]}
    wall_with_apertures(root,utility,SITE_GRADE,8.9-SITE_GRADE,node,stucco,.25)
    wall_piece(root,"site_rear_utility_north",(0,rear_y),(0,outer_y),SITE_GRADE,8.9,.25,node,stucco)
    wall_piece(root,"site_rear_utility_partition",(4.5,rear_y),(4.5,outer_y),SITE_GRADE,8.9,.25,node,stucco)
    frame_opening(root,"site_rear_utility_door",(1,53.18),(3.5,53.18),0,6+8/12,SITE_GRADE,node,utility_door,utility_door,"door",depth=.18,leaf_material=utility_door)


def rear_stairs(root, parent, wood):
    """Photo-supported rear platform and switchback stair with inferred dimensions."""
    node=empty(root,"site_rear_exterior_stair",parent); node["dimensions"]="inferred from listing photos 18-21"
    # Short flight moves away from the rear wall to the switchback landing.
    for i in range(4):
        y1=57.31+i*.75; y2=y1+.75; z=10-(i+1)*.55
        prism(root,f"site_rear_stair_upper_{i:02}",[(14,y1),(18,y1),(18,y2),(14,y2)],z-.15,z,node,wood)
    prism(root,"site_rear_switchback_landing",[(14,60.31),(18,60.31),(18,64.31),(14,64.31)],7.8,7.95,node,wood)
    # Photo 19 fixes the long flight parallel to the facade toward model -X.
    steps=19
    lower_drop=7.8-SITE_GRADE
    for i in range(steps):
        x2=14-i*13/steps; x1=14-(i+1)*13/steps; z=7.8-(i+1)*lower_drop/steps
        prism(root,f"site_rear_stair_lower_{i:02}",[(x1,60.31),(x2,60.31),(x2,64.31),(x1,64.31)],z-.15,z,node,wood)
    for y in (60.31,64.31):
        beam3d(root,f"site_rear_stair_lower_rail_{y}",(14,y,11.3),(1,y,SITE_GRADE+3.5),.18,node,wood)
        beam3d(root,f"site_rear_stair_lower_midrail_{y}",(14,y,10.15),(1,y,SITE_GRADE+2.35),.14,node,wood)
        beam3d(root,f"site_rear_stair_lower_lowrail_{y}",(14,y,9.05),(1,y,SITE_GRADE+1.25),.14,node,wood)
        for index in range(0,steps+1,4):
            x=14-index*13/steps
            tread=7.8-index*lower_drop/steps
            rail=11.3-index*lower_drop/steps
            beam3d(root,f"site_rear_stair_lower_post_{y}_{index}",(x,y,tread),(x,y,rail),.20,node,wood)
    for y1,y2,label in ((60.67,60.91,"inner"),(63.71,63.95,"outer")):
        profile_y(root,f"site_rear_stair_lower_stringer_{label}",[(14,7.75),(14,6.85),(1,SITE_GRADE-.55),(1,SITE_GRADE+.35)],y1,y2,node,wood)
    for x in (14,18):
        beam3d(root,f"site_rear_stair_upper_rail_{x}",(x,57.31,13.5),(x,60.31,11.3),.18,node,wood)
        beam3d(root,f"site_rear_stair_upper_midrail_{x}",(x,57.31,12.15),(x,60.31,10.25),.14,node,wood)
        beam3d(root,f"site_rear_stair_upper_lowrail_{x}",(x,57.31,11.1),(x,60.31,9.2),.14,node,wood)
        for index in range(4):
            y=57.31+index
            tread=9.75-(index+1)*.45
            rail=13.5-index*2.2/3
            beam3d(root,f"site_rear_stair_upper_post_{x}_{index}",(x,y,tread),(x,y,rail),.20,node,wood)
    for x1,x2,label in ((14.25,14.5,"inner"),(17.5,17.75,"outer")):
        mesh(root,f"site_rear_stair_upper_stringer_{label}",[(x1,57.31,9.95),(x2,57.31,9.95),(x2,57.31,9.15),(x1,57.31,9.15),(x1,60.31,7.35),(x2,60.31,7.35),(x2,60.31,8.15),(x1,60.31,8.15)],[(0,1,2,3),(4,7,6,5),(0,4,5,1),(3,2,6,7),(1,5,6,2),(0,3,7,4)],node,wood)
    open_guard(root,"site_rear_switch_guard_outer",(14,64.31),(18,64.31),7.95,node,wood,posts=2)
    open_guard(root,"site_rear_switch_guard_end",(18,60.31),(18,64.31),7.95,node,wood,posts=2)
    for label,x,y,height in [("switch_n",14.2,60.51,7.8),("switch_s",17.8,64.11,7.8)]:
        beam3d(root,f"site_rear_stair_post_{label}",(x,y,SITE_GRADE),(x,y,height),.28,node,wood)
    # Readable deck construction from photos 18-21: fascia, joists, posts and braces.
    wall_piece(root,"site_rear_deck_fascia",(-.15,57.31),(19,57.31),9.15,10.0,.45,parent,wood)
    for x in range(1,20,2):
        wall_piece(root,f"site_rear_deck_joist_{x}",(x,49.35),(x,57.41),9.25,9.94,.22,parent,wood)
    for x in (1,7,13,19):
        beam3d(root,f"site_rear_deck_support_{x}",(x,56.88,SITE_GRADE),(x,56.88,9.5),.42,parent,wood)
    for index,(a,b) in enumerate([((1,56.88,2),(7,56.88,9.35)),((7,56.88,2),(13,56.88,9.35)),((13,56.88,2),(19,56.88,9.35))]):
        beam3d(root,f"site_rear_deck_brace_{index}",a,b,.26,parent,wood)


def detached(root, roofs, stucco, roof, trim, glass, soffit, roof_trim, door_leaf):
    node=empty(root,"site_detached_unit")
    node.location.z=(SITE_GRADE+.16)*FT
    node["source"]="A1.0 and supplemental A2.3 dated 2023-04-03"
    node["rotation_note"]="12ft dimension follows parcel; 17ft11in dimension runs across parcel; entry faces south"
    floor=[(DETACHED_WEST_X,DETACHED_FRONT_Y),(DETACHED_EAST_X,DETACHED_FRONT_Y),(DETACHED_EAST_X,DETACHED_REAR_Y),(DETACHED_WEST_X,DETACHED_REAR_Y)]
    prism(root,"site_detached_floor",floor,-.22,0,node,stucco)
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
        for i,a in enumerate(spec["apertures"]):
            frame_opening(root,f"{spec['id']}_frame_{i}",start+d*a["start"],start+d*a["end"],a["bottom"],a["top"],0,node,trim,glass,a["kind"],depth=.28,recess=.12,reveals=True,casing_offset=.22,leaf_material=door_leaf)
            if a["kind"]=="window": opening_bars(root,f"{spec['id']}_frame_{i}",start+d*a["start"],start+d*a["end"],a["bottom"]+.12,a["top"]-.12,0,node,trim,1,2,.08)
    # A2.3 washroom is an L in the north/east corner after site rotation.
    bath_south_x=DETACHED_WEST_X+5/12+6+8/12+5/24
    bath_west_y=DETACHED_FRONT_Y+5/12+4+8/12+5/24
    wall_with_apertures(root,{"id":"site_detached_bath_south","start":(bath_south_x,bath_west_y),"end":(bath_south_x,DETACHED_REAR_Y-5/12),"apertures":[]},0,8+0.5/12,node,stucco,5/12)
    wall_with_apertures(root,{"id":"site_detached_bath_west","start":(DETACHED_WEST_X+5/12,bath_west_y),"end":(bath_south_x,bath_west_y),"apertures":[{"kind":"door","start":3+10/12,"end":6+6/12,"bottom":0,"top":6+8/12}]},0,8+0.5/12,node,stucco,5/12)
    gable_roof_finish(roofs,"site_detached_roof",DETACHED_WEST_X,DETACHED_EAST_X,DETACHED_FRONT_Y,DETACHED_REAR_Y,8+0.5/12,12+1/12,node,roof,soffit,roof_trim)
    detached_wall_roof_z=8+0.5/12+(12+1/12-(8+0.5/12))*.7/(DETACHED_WIDTH/2+.7)
    for label,y1,y2 in (("west",DETACHED_FRONT_Y-.01,DETACHED_FRONT_Y+.01),("east",DETACHED_REAR_Y-.01,DETACHED_REAR_Y+.01)):
        profile_y(root,f"site_detached_gable_{label}",[(DETACHED_WEST_X,8+0.5/12),(DETACHED_WEST_X,detached_wall_roof_z),((DETACHED_WEST_X+DETACHED_EAST_X)/2,12+1/12),(DETACHED_EAST_X,detached_wall_roof_z),(DETACHED_EAST_X,8+0.5/12)],y1,y2,node,stucco)
    for label,y in (("front",DETACHED_FRONT_Y-.025),("rear",DETACHED_REAR_Y+.025)):
        vertical_disc(root,f"site_detached_gable_louver_{label}",((DETACHED_WEST_X+DETACHED_EAST_X)/2,y,10.35),.48,"y",node,trim)
        for index,z in enumerate((10.1,10.35,10.6)):
            width=.68*(1-abs(z-10.35)/.62)
            wall_piece(root,f"site_detached_gable_louver_{label}_slot_{index}",((DETACHED_WEST_X+DETACHED_EAST_X)/2-width/2,y-.02),((DETACHED_WEST_X+DETACHED_EAST_X)/2+width/2,y-.02),z-.035,z+.035,.05,node,soffit)
    for side,x in (("west",DETACHED_WEST_X),("east",DETACHED_EAST_X)):
        wall_piece(roofs,f"site_detached_eave_closure_{side}",(x,DETACHED_FRONT_Y),(x,DETACHED_REAR_Y),8+0.5/12,detached_wall_roof_z,.12,node,soffit)
    for side,x,direction in (("west",DETACHED_WEST_X,-1),("east",DETACHED_EAST_X,1)):
        for index in range(9):
            y=DETACHED_FRONT_Y+.35+index*(DETACHED_ALONG-.7)/8
            beam3d(roofs,f"site_detached_rafter_tail_{side}_{index}",(x-direction*.05,y,7.82),(x+direction*.82,y,7.82),.13,node,roof_trim)


def garage(root, roofs, siding, roof, trim, gray_door, blue_door, soffit):
    node=empty(root,"site_garage"); node["source"]="A1.0 footprint and listing photo 22"; node["height"]="inferred from photo"
    node.location.z=(SITE_GRADE+.16)*FT
    outline=[(GARAGE_WEST_X,GARAGE_FRONT_Y),(GARAGE_EAST_X,GARAGE_FRONT_Y),(GARAGE_EAST_X,GARAGE_REAR_Y),(GARAGE_WEST_X,GARAGE_REAR_Y)]
    prism(root,"site_garage_slab",outline,-.2,0,node,siding)
    h=.35/2
    wall_outline=[(GARAGE_WEST_X+h,GARAGE_FRONT_Y+h),(GARAGE_EAST_X-h,GARAGE_FRONT_Y+h),(GARAGE_EAST_X-h,GARAGE_REAR_Y-h),(GARAGE_WEST_X+h,GARAGE_REAR_Y-h)]
    front={"id":"site_garage_front","start":wall_outline[0],"end":wall_outline[1],"apertures":[
        {"kind":"door","start":1.15,"end":4.35,"bottom":0,"top":6.85},
        {"kind":"door","start":7.25,"end":10.25,"bottom":0,"top":6.85},
    ]}
    wall_with_apertures(root,front,0,8,node,siding,.35)
    for i,(a,b) in enumerate(zip(wall_outline[1:],wall_outline[2:]+wall_outline[:1])): wall_piece(root,f"site_garage_wall_{i+1}",a,b,0,8,.35,node,siding)
    start=Vector(front["start"]); d=(Vector(front["end"])-start).normalized()
    for index,(opening,mat) in enumerate(zip(front["apertures"],(gray_door,blue_door))):
        frame_opening(root,f"site_garage_front_door_{index}",start+d*opening["start"],start+d*opening["end"],0,opening["top"],0,node,trim,mat,"door",depth=.20,recess=.08,reveals=True,inward=(0,1),casing_offset=.20,leaf_material=mat)
    gable_roof_finish(roofs,"site_garage_roof",GARAGE_WEST_X,GARAGE_EAST_X,GARAGE_FRONT_Y,GARAGE_REAR_Y,8.2,10.8,node,roof,soffit,trim)
    garage_wall_roof_z=8.2+(10.8-8.2)*.7/(GARAGE_WIDTH/2+.7)
    for label,y1,y2 in (("front",GARAGE_FRONT_Y-.01,GARAGE_FRONT_Y+.01),("rear",GARAGE_REAR_Y-.01,GARAGE_REAR_Y+.01)):
        profile_y(root,f"site_garage_gable_{label}",[(GARAGE_WEST_X,8),(GARAGE_WEST_X,garage_wall_roof_z),((GARAGE_WEST_X+GARAGE_EAST_X)/2,10.8),(GARAGE_EAST_X,garage_wall_roof_z),(GARAGE_EAST_X,8)],y1,y2,node,siding)
    for side,x in (("west",GARAGE_WEST_X),("east",GARAGE_EAST_X)):
        wall_piece(roofs,f"site_garage_eave_closure_{side}",(x,GARAGE_FRONT_Y),(x,GARAGE_REAR_Y),8,garage_wall_roof_z,.12,node,soffit)
    # Photo 22: vertical gable boards, horizontal long-wall boards and open eave tails.
    for index in range(14):
        x=GARAGE_WEST_X+.25+index*(GARAGE_WIDTH-.5)/13
        ridge_z=8+(10.8-8)*(1-abs(x-(GARAGE_WEST_X+GARAGE_WIDTH/2))/(GARAGE_WIDTH/2))
        door_top=next((opening["top"] for opening in front["apertures"] if GARAGE_WEST_X+opening["start"]<=x<=GARAGE_WEST_X+opening["end"]),0)
        segments=[(door_top,ridge_z)] if door_top else [(0,ridge_z)]
        if abs(x-(GARAGE_WEST_X+GARAGE_WIDTH/2))<.75:
            segments=[(z1,min(z2,8.82)) for z1,z2 in segments if z1<8.82]+[(10.25,ridge_z)]
        for segment,zs in enumerate(segments):
            z1,z2=zs
            if z2>z1:
                wall_piece(root,f"site_garage_gable_board_{index}_{segment}",(x-.018,GARAGE_FRONT_Y-.04),(x+.018,GARAGE_FRONT_Y-.04),z1,z2,.02,node,siding)
    for side,x in (("west",GARAGE_WEST_X-.19),("east",GARAGE_EAST_X+.19)):
        for index,z in enumerate([.5+i*.55 for i in range(14)]):
            wall_piece(root,f"site_garage_siding_{side}_{index}",(x,GARAGE_FRONT_Y),(x,GARAGE_REAR_Y),z,z+.055,.05,node,trim)
        for index in range(12):
            y=GARAGE_FRONT_Y+.45+index*(GARAGE_ALONG-.9)/11
            beam3d(roofs,f"site_garage_rafter_tail_{side}_{index}",(x,y,7.98),(x+(-.72 if side=="west" else .72),y,7.98),.13,node,trim)
    vertical_disc(root,"site_garage_front_louver",((GARAGE_WEST_X+GARAGE_EAST_X)/2,GARAGE_FRONT_Y-.22,9.55),.65,"y",node,trim,3)
    for index,(z,width) in enumerate(((9.27,.66),(9.48,.92),(9.69,.70))):
        wall_piece(root,f"site_garage_front_louver_slot_{index}",((GARAGE_WEST_X+GARAGE_EAST_X)/2-width/2,GARAGE_FRONT_Y-.25),((GARAGE_WEST_X+GARAGE_EAST_X)/2+width/2,GARAGE_FRONT_Y-.25),z-.04,z+.04,.05,node,soffit)


def site_surfaces(root, ground, concrete, landscape):
    node=empty(root,"site_parcel")
    # Owner-confirmed grade remains roughly level around the house and site.
    x1,x2=PROPERTY_WEST_X,PROPERTY_EAST_X; y1,y2=PROPERTY_FRONT_Y,PROPERTY_REAR_Y
    prism(root,"site_ground",[(x1,y1),(x2,y1),(x2,y2),(x1,y2)],SITE_GRADE-.10,SITE_GRADE,node,ground)
    paving_bottom,paving_top=SITE_GRADE-.10,SITE_GRADE+.02
    planting_bottom,planting_top=SITE_GRADE-.09,SITE_GRADE+.01
    # A1.0-supported circulation and parking zones at diagrammatic detail.
    prism(root,"site_front_walk",[(11,PROPERTY_FRONT_Y),(16,PROPERTY_FRONT_Y),(16,-7),(11,-7)],paving_bottom,paving_top,node,concrete)
    prism(root,"site_north_side_walk",[(-3,0),(0,0),(0,73),(-3,73)],paving_bottom,paving_top,node,concrete)
    # A1.0 shows a continuous 10ft south passage and concrete connections
    # around planted courtyard islands rather than a single paved courtyard.
    prism(root,"site_south_passage",[(35,0),(45,0),(45,91.5),(35,91.5)],paving_bottom,paving_top,node,concrete)
    prism(root,"site_courtyard_cross_walk",[(0,50),(35,50),(35,55),(0,55)],paving_bottom,paving_top,node,concrete)
    prism(root,"site_courtyard_north_walk",[(0,73),(35,73),(35,78),(0,78)],paving_bottom,paving_top,node,concrete)
    prism(root,"site_courtyard_center_walk",[(15,55),(20,55),(20,73),(15,73)],paving_bottom,paving_top,node,concrete)
    prism(root,"site_detached_entry_walk",[(DETACHED_EAST_X,86.5),(35,86.5),(35,91.5),(DETACHED_EAST_X,91.5)],paving_bottom,paving_top,node,concrete)
    for label,outline in [
        ("front",[(DETACHED_WEST_X-2,DETACHED_FRONT_Y-5),(DETACHED_EAST_X+2,DETACHED_FRONT_Y-5),(DETACHED_EAST_X+2,DETACHED_FRONT_Y),(DETACHED_WEST_X-2,DETACHED_FRONT_Y)]),
        ("west",[(DETACHED_WEST_X-2,DETACHED_FRONT_Y),(DETACHED_WEST_X,DETACHED_FRONT_Y),(DETACHED_WEST_X,DETACHED_REAR_Y+3),(DETACHED_WEST_X-2,DETACHED_REAR_Y+3)]),
        ("east",[(DETACHED_EAST_X,DETACHED_FRONT_Y),(DETACHED_EAST_X+2,DETACHED_FRONT_Y),(DETACHED_EAST_X+2,DETACHED_REAR_Y+6),(DETACHED_EAST_X,DETACHED_REAR_Y+6)]),
        ("rear",[(DETACHED_WEST_X-2,DETACHED_REAR_Y),(DETACHED_EAST_X+2,DETACHED_REAR_Y),(DETACHED_EAST_X+2,DETACHED_REAR_Y+3),(DETACHED_WEST_X-2,DETACHED_REAR_Y+3)]),
    ]: prism(root,f"site_detached_walk_{label}",outline,paving_bottom,paving_top,node,concrete)
    prism(root,"site_rear_access",[(PROPERTY_WEST_X,GARAGE_FRONT_Y-5),(PROPERTY_EAST_X,GARAGE_FRONT_Y-5),(PROPERTY_EAST_X,PROPERTY_REAR_Y),(PROPERTY_WEST_X,PROPERTY_REAR_Y)],paving_bottom,paving_top,node,concrete)
    prism(root,"site_rear_yard_walk",[(19,99.5),(24,99.5),(24,GARAGE_FRONT_Y-5),(19,GARAGE_FRONT_Y-5)],paving_bottom,paving_top,node,concrete)
    for i in range(3):
        x1=13+i*8.1
        stall=prism(root,f"site_parking_stall_{i+1}",[(x1,GARAGE_FRONT_Y),(x1+8.1,GARAGE_FRONT_Y),(x1+8.1,GARAGE_REAR_Y),(x1,GARAGE_REAR_Y)],paving_bottom,paving_top,node,concrete)
        stall["dimensions"]="8ft1in source width; alongside garage over its source footprint depth"
    for i,(x1,x2,y1,y2) in enumerate([
        (-4,1,-20,-7),(17,35,-20,-7),(-4,1,-3,0),(17,35,-3,45),
        (2,15,55,73),(20,33,55,73),(20,35,78,86.5),(24,35,91.5,128),(1,18,99.5,128),(-4,-2,73,145),
    ]):
        prism(root,f"site_landscape_zone_{i}",[(x1,y1),(x2,y1),(x2,y2),(x1,y2)],planting_bottom,planting_top,node,landscape)


def main():
    if not bpy.data.filepath: raise RuntimeError("Load the Sage master before applying the site updater")
    if not bpy.data.collections.get("HOUSE_LAYOUT"): raise RuntimeError("HOUSE_LAYOUT is required")
    root=owned_collection(OWNED); roofs=owned_collection(ROOFS,root)
    authoring=bpy.data.collections.get("AUTHORING") or bpy.context.scene.collection
    cams=owned_collection(CAMERAS,authoring)
    stucco=material("site_stucco",(.72,.70,.65)); roof=material("site_roof",(.14,.16,.17)); wood=material("site_wood",(.34,.12,.06)); glass=material("site_glass",(.18,.38,.48),.2)
    detached_trim=material("site_detached_cyan_trim",(.08,.48,.56),.55); detached_soffit=material("site_detached_soffit",(.76,.75,.70)); detached_roof_trim=material("site_detached_roof_trim",(.82,.82,.78)); detached_door=material("site_detached_door",(.82,.81,.75))
    garage_trim=material("site_garage_white_trim",(.78,.79,.76)); garage_gray=material("site_garage_gray_door",(.36,.39,.40)); garage_blue=material("site_garage_blue_door",(.04,.42,.55)); garage_soffit=material("site_garage_soffit",(.68,.69,.66))
    main_stucco=material("main_house_stucco",(.78,.76,.69)); main_roof=material("main_house_roof",(.62,.60,.55)); main_soffit=material("main_house_soffit",(.64,.63,.59)); main_trim=material("main_house_blue_green_trim",(.08,.38,.41),.55); terracotta=material("main_house_terracotta",(.55,.18,.08),.7); deck_wood=material("main_house_deck_wood",(.38,.10,.055),.7); metal=material("main_house_dark_metal",(.055,.065,.06),.45)
    glass.metallic=.05; ground=material("site_ground",(.20,.28,.13)); concrete=material("site_concrete",(.42,.43,.40)); landscape=material("site_landscape",(.14,.31,.10)); siding=material("site_garage_siding",(.52,.55,.54))
    site_surfaces(root,ground,concrete,landscape); main_house_exterior(root,roofs,main_stucco,main_roof,main_soffit,main_trim,glass,terracotta,deck_wood,metal,concrete,garage_trim); detached(root,roofs,stucco,roof,detached_trim,glass,detached_soffit,detached_roof_trim,detached_door); garage(root,roofs,siding,roof,garage_trim,garage_gray,garage_blue,garage_soffit)
    camera(cams,"site_plan",(20,68,245),(20,68,0),210)
    camera(cams,"site_perspective_front",(-72,-80,62),(17,38,8))
    camera(cams,"site_perspective_rear",(92,210,72),(20,105,7))
    camera(cams,"site_main_front",(16,-70,22),(16,8,12))
    camera(cams,"site_main_rear",(64,94,25),(17,45,10))
    camera(cams,"site_exterior_front",(7.6,-26.3,2.55),(7.6,3,2.55),lens=17)
    camera(cams,"site_exterior_porch",(5.5,-10.2,2.35),(9.5,1,2.35),lens=17,shift_y=.01)
    camera(cams,"site_exterior_rear_stairs",(33,72,5.1),(13,54,5),lens=17)
    camera(cams,"site_exterior_rear_support",(-2,75,5.1),(10,55,7),lens=19)
    camera(cams,"site_exterior_rear_patio",(12,66,3.5),(11,52,4.2),lens=35)
    camera(cams,"site_exterior_front_diagnostic",(16,-47,9),(16,8,10),lens=34)
    camera(cams,"site_exterior_rear_diagnostic",(50,88,8),(18,52,8),lens=32)
    camera(cams,"site_main_roof_plan",(16,29,85),(16,29,18),74)
    camera(cams,"site_detached_plan",((DETACHED_WEST_X+DETACHED_EAST_X)/2,(DETACHED_FRONT_Y+DETACHED_REAR_Y)/2,45),((DETACHED_WEST_X+DETACHED_EAST_X)/2,(DETACHED_FRONT_Y+DETACHED_REAR_Y)/2,0),25)
    camera(cams,"site_exterior_north",(-58,26,14),(0,26,8),lens=30)
    camera(cams,"site_exterior_south",(93,25,14),(31,25,8),lens=30)
    camera(cams,"site_exterior_south_reference",(49,-12,9),(32.7,19,8),lens=31,shift_y=.08)
    camera(cams,"site_exterior_detached",(41,72,10+SITE_GRADE+.16),(9,88,6+SITE_GRADE+.16),lens=34)
    camera(cams,"site_exterior_garage",(39,108,8+SITE_GRADE+.16),(3.5,GARAGE_FRONT_Y,5+SITE_GRADE+.16),lens=30)
    camera(cams,"site_exterior_circulation",(58,112,72),(17,82,0),lens=42)
    bpy.context.scene["site_layout_source"]="A1.0, A2.2, A3.0/A3.1, A0.5, supplemental A2.3, photos 18-22"
    bpy.context.scene["site_layout_ownership"]="SITE_LAYOUT, SITE_ROOFS and SITE_LAYOUT_CAMERAS"
    bpy.context.scene["site_layout_revision"]=1
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    print(f"Updated full site in {bpy.data.filepath}")


if __name__=="__main__":
    try: main()
    except Exception as exc: print(f"ERROR: {exc}",file=sys.stderr); raise
