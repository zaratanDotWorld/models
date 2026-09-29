"""Focused native checks for the separately owned Sage site geometry."""

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sage_site_layout import *


def close(actual, expected, tolerance, label):
    if abs(actual-expected)>tolerance: raise AssertionError(f"{label}: {actual} != {expected} within {tolerance}")


def world_bounds(name):
    obj=bpy.data.objects[name]
    points=[obj.matrix_world @ __import__('mathutils').Vector(corner) for corner in obj.bound_box]
    return tuple(min(p[i] for p in points) for i in range(3)),tuple(max(p[i] for p in points) for i in range(3))


def size_ft(name):
    low,high=world_bounds(name)
    return tuple((high[i]-low[i])/FT for i in range(3))


def downward_hit(x, y, z=20):
    hit, position, _normal, _face, obj, _matrix = bpy.context.scene.ray_cast(
        bpy.context.evaluated_depsgraph_get(), Vector((x*FT,y*FT,z*FT)),
        Vector((0,0,-1)), distance=40*FT)
    if not hit: raise AssertionError(f"No surface below ({x}, {y})")
    return obj.name, position.z/FT


def forward_hit(x, y, z):
    hit, position, _normal, _face, obj, _matrix = bpy.context.scene.ray_cast(
        bpy.context.evaluated_depsgraph_get(), Vector((x*FT,y*FT,z*FT)),
        Vector((0,1,0)), distance=2*FT)
    if not hit: raise AssertionError(f"No surface ahead of ({x}, {y}, {z})")
    return obj.name, position.y/FT


def lateral_hit(x, y, z, direction, distance=1.2):
    hit,position,_normal,_face,obj,_matrix=bpy.context.scene.ray_cast(
        bpy.context.evaluated_depsgraph_get(),Vector((x,y,z))*FT,
        Vector((direction,0,0)),distance=distance*FT)
    if not hit: raise AssertionError(f"No lateral closure from ({x}, {y}, {z})")
    return obj.name,position.x/FT


def main():
    for name in ["SITE_LAYOUT","SITE_ROOFS","SITE_LAYOUT_CAMERAS"]:
        if not bpy.data.collections.get(name): raise AssertionError(f"Missing {name}")
    close(longitudinal_chain(),PARCEL_LENGTH,1e-8,"A1.0 longitudinal chain")
    parcel_x,parcel_y,_=size_ft("site_ground"); close(parcel_x,PARCEL_WIDTH,.02,"parcel width"); close(parcel_y,PARCEL_LENGTH,.02,"parcel length")
    sx,sy,_=size_ft("site_detached_floor"); close(sx,DETACHED_WIDTH,.02,"detached across parcel"); close(sy,DETACHED_ALONG,.02,"detached along parcel")
    sx,sy,_=size_ft("site_garage_slab"); close(sx,GARAGE_WIDTH,.02,"garage across parcel"); close(sy,GARAGE_ALONG,.02,"garage along parcel")
    rear_parts=[obj for obj in bpy.data.collections["HOUSE_LAYOUT"].all_objects if obj.name.startswith("g_rear_") and obj.type=="MESH"]
    house_rear=max((obj.matrix_world @ __import__('mathutils').Vector(c)).y/FT for obj in rear_parts for c in obj.bound_box)
    detached_low,_=world_bounds("site_detached_floor"); garage_low,garage_high=world_bounds("site_garage_slab"); ground_low,ground_high=world_bounds("site_ground")
    close(ground_high[2]/FT,SITE_GRADE,.02,"owner-confirmed site grade")
    close(detached_low[1]/FT-house_rear,HOUSE_TO_UNIT,.15,"saved house to detached separation")
    close(garage_low[1]/FT-(detached_low[1]/FT+DETACHED_ALONG),UNIT_TO_GARAGE,.03,"saved detached to garage separation")
    close(ground_high[1]/FT-garage_high[1]/FT,ALLEY_SETBACK,.03,"saved garage alley setback")
    close(detached_low[0]/FT-PROPERTY_WEST_X,5,.03,"detached north setback")
    close(garage_low[0]/FT-PROPERTY_WEST_X,2,.03,"garage north setback")
    close(world_bounds("site_detached_floor")[1][2]/FT,SITE_GRADE+.16,.02,"detached slab at grade")
    close(world_bounds("site_garage_slab")[1][2]/FT,SITE_GRADE+.16,.02,"garage slab at grade")
    if bpy.data.objects.get("site_front_step_bank_left") or bpy.data.objects.get("site_front_step_bank_right"):
        raise AssertionError("Invented front step banks remain")
    for name in ["site_roof_main_complex","site_roof_front_porch","site_roof_rear_pitch_break","site_detached_roof","site_garage_roof","site_rear_exterior_stair"]:
        if name not in bpy.data.objects: raise AssertionError(f"Missing {name}")
    expected_doors={
        "site_rear_utility_door_leaf":(2.5,6+8/12),
        "site_frame_g_rear_2_leaf":(98/37.046,7),
        "site_frame_g_foyer_entry_0_leaf":(104/37.046,7),
        "site_frame_g_foyer_entry_1_leaf":(105/37.046,7),
        "site_frame_u_rear_1_leaf":(110/37,7),
        "site_detached_south_entry_frame_0_leaf":(3,6+8/12),
        "site_garage_front_door_0_leaf":(3.2,6.85),
        "site_garage_front_door_1_leaf":(3,6.85),
    }
    leaves={obj.name for obj in bpy.data.collections["SITE_LAYOUT"].all_objects if obj.name.endswith("_leaf")}
    if leaves!=set(expected_doors): raise AssertionError(f"Exterior door leaves differ: {sorted(leaves)}")
    for name,(width,height) in expected_doors.items():
        dimensions=sorted(size_ft(name))
        close(dimensions[-2],width,.02,f"{name} scheduled width")
        close(dimensions[-1],height,.02,f"{name} scheduled height")
        if bpy.data.objects[name].get("pose")!="closed": raise AssertionError(f"{name} has no deliberate pose")
    if "site_frame_u_rear_3_glass" in bpy.data.objects:
        raise AssertionError("Confirmed unbuilt rear window 207.2 still has an exterior frame")
    for name in ["site_rear_switch_guard_outer_rail_0","site_rear_stair_lower_post_60.31_0","site_rear_stair_upper_post_14_0","site_front_porch_curve_left","site_front_porch_curve_right"]:
        if name not in bpy.data.objects:
            raise AssertionError(f"Missing connected exterior detail {name}")
    omitted_wall=bpy.data.objects.get("u_rear_solid_end")
    if not omitted_wall or size_ft(omitted_wall.name)[0]<5.5:
        raise AssertionError("Rear wall does not infill the confirmed unbuilt 207.2 opening")
    left_curve_low,left_curve_high=world_bounds("site_front_porch_curve_left")
    left_column_low,left_column_high=world_bounds("site_front_porch_pier_left")
    header_low,header_high=world_bounds("site_front_porch_header")
    if left_curve_low[0]>left_column_high[0]+.02 or left_curve_high[0]<header_low[0]-.02:
        raise AssertionError("Porch curve does not connect its column and header")
    header_hit,header_y=forward_hit(8,-4,8.4)
    if header_hit!="site_front_porch_header" or abs(header_y+3.25)>.02:
        raise AssertionError(f"Porch spandrel is open: {header_hit} at {header_y:.3f}ft")
    side_hit,side_position,_normal,_face,side_obj,_matrix=bpy.context.scene.ray_cast(
        bpy.context.evaluated_depsgraph_get(),Vector((1*FT,0,4*FT)),Vector((1,0,0)),distance=2.5*FT)
    if side_hit and side_obj.name.startswith("site_front_porch"):
        raise AssertionError(f"Porch side opening is blocked by {side_obj.name} at X={side_position.x/FT:.3f}ft")
    for y in (60.31,64.31):
        posts=[obj for obj in bpy.data.objects if obj.name.startswith(f"site_rear_stair_lower_post_{y}_")]
        if len(posts)!=5:
            raise AssertionError(f"Rear stair rail at {y} has {len(posts)} posts")
        for post in posts:
            post_low,post_high=world_bounds(post.name)
            if post_high[2]-post_low[2]<1.5*FT:
                raise AssertionError(f"Rear stair rail post {post.name} does not connect tread and rail")
    for glass_name,trim_name,axis,direction in [
        ("site_frame_u_bed5_front_1_glass","site_frame_u_bed5_front_1_top",1,1),
        ("site_frame_g_rear_3_glass","site_frame_g_rear_3_top",1,-1),
        ("site_frame_g_east_rear_0_glass","site_frame_g_east_rear_0_top",0,-1),
    ]:
        glass_low,glass_high=world_bounds(glass_name); trim_low,trim_high=world_bounds(trim_name)
        glass_center=(glass_low[axis]+glass_high[axis])/2
        trim_center=(trim_low[axis]+trim_high[axis])/2
        if direction*(glass_center-trim_center)<.10*FT:
            raise AssertionError(f"{glass_name} is not recessed inward behind its exterior trim")
    fascia_low,fascia_high=world_bounds("site_rear_deck_fascia")
    for x in (1,7,13,19):
        joist_low,joist_high=world_bounds(f"site_rear_deck_joist_{x}")
        support_low,support_high=world_bounds(f"site_rear_deck_support_{x}")
        if joist_high[2]<9.92*FT or support_high[2]<joist_low[2] or support_high[1]<fascia_low[1]:
            raise AssertionError(f"Rear deck support at {x} does not contact deck, joist, and fascia")
    for label,inner_x,y1,y2 in [("dining",32.68,15.0,27.8),("rear_south",30.82,39.8,49.5)]:
        name=f"site_roof_south_{label}_shed"; low,high=world_bounds(name)
        close(low[0]/FT,inner_x,.02,f"{label} shed inner edge")
        close(high[0]/FT,34.25,.02,f"{label} shed outer edge")
        close(low[1]/FT,y1,.02,f"{label} shed start")
        close(high[1]/FT,y2,.02,f"{label} shed end")
        if high[2]/FT>=10: raise AssertionError(f"{name} intrudes above the upper-floor datum")
    for name in ["site_skin_detail_living_solid_0","site_skin_detail_dining_solid_0","site_roof_main_complex_soffit","site_roof_frieze_north","site_detached_roof_soffit","site_garage_roof_soffit","site_garage_front_louver"]:
        if name not in bpy.data.objects:
            raise AssertionError(f"Missing exterior completion geometry {name}")
    old_glass=bpy.data.objects["C_living_side_glass"]
    new_glass=bpy.data.objects["site_frame_detail_living_0_glass"]
    old_high=max((old_glass.matrix_world @ Vector(corner)).x for corner in old_glass.bound_box)
    new_low=min((new_glass.matrix_world @ Vector(corner)).x for corner in new_glass.bound_box)
    casing_high=max((bpy.data.objects["site_frame_detail_living_0_top"].matrix_world @ Vector(corner)).x for corner in bpy.data.objects["site_frame_detail_living_0_top"].bound_box)
    if new_low<=old_high or casing_high<=new_low:
        raise AssertionError("Detailed living exterior glazing is not between protected glass and new casing")
    soffit_low,_=world_bounds("site_roof_north_soffit")
    frieze_low,frieze_high=world_bounds("site_roof_frieze_north")
    if frieze_low[2]/FT>18.51 or frieze_high[2]<soffit_low[2]:
        raise AssertionError("Main north roof frieze does not close the wall-to-soffit band")
    for name,x1,x2 in [("site_detached_gable_west",DETACHED_WEST_X,DETACHED_EAST_X),("site_garage_gable_front",GARAGE_WEST_X,GARAGE_EAST_X)]:
        low,high=world_bounds(name)
        if low[0]/FT<x1-.02 or high[0]/FT>x2+.02:
            raise AssertionError(f"{name} extends through the roof overhang")
    for x,y,z,direction,prefix in [
        (33.3,20,18.75,-1,"site_roof_frieze_south"),
        (-.6,20,18.75,1,"site_roof_frieze_north"),
        (18.0,88,8.07+SITE_GRADE+.16,-1,"site_detached_eave_closure_east"),
        (10.2,150,8.12+SITE_GRADE+.16,-1,"site_garage_eave_closure_east"),
        (31.25,45,18.75,-1,"site_roof_rear_pitch_inner_south_closure"),
        (19,88,8+SITE_GRADE+.16,-1,"site_detached_roof_eave_east"),
        (11,150,8.16+SITE_GRADE+.16,-1,"site_garage_roof_eave_east"),
    ]:
        hit,_=lateral_hit(x,y,z,direction)
        if hit!=prefix:
            raise AssertionError(f"Roof-to-wall join hit {hit}, expected {prefix}")
    for x,y,z,prefix in [
        (34,.2,5,"site_skin_detail_living"),
        (35,20,9.05,"site_skin_detail_dining"),
        (35,8,9.05,"site_skin_detail_living"),
        (35,15.15,5,"site_skin_detail_dining"),
    ]:
        hit,_=lateral_hit(x,y,z,-1,5)
        if not hit.startswith(prefix):
            raise AssertionError(f"Detailed side finish seam hit {hit}, expected {prefix}")
    for x,y,z,direction,prefix in [
        (-1,10,-1,1,"site_base_g_west"),
        (34,8,-1,-1,"site_base_detail_living"),
        (35,14.9,-1,-1,"site_base_detail_living"),
    ]:
        hit,_=lateral_hit(x,y,z,direction,5)
        if not hit.startswith(prefix):
            raise AssertionError(f"Main house base hit {hit}, expected {prefix}")
    rear_base,_=forward_hit(10,48,-1)
    if not rear_base.startswith("site_base_g_rear"):
        raise AssertionError(f"Rear house base is open: {rear_base}")
    patio_hit,patio_z=downward_hit(16,51,1)
    if patio_hit not in {"site_rear_patio_slab","site_rear_patio_base"} or abs(patio_z)>.02:
        raise AssertionError(f"Rear patio misses the ground-door threshold: {patio_hit} at {patio_z:.3f}ft")
    for index,(x,z) in enumerate([(19.5,-.55),(20.5,-1.1),(21.5,-1.65),(22.5,-2.2)]):
        hit,actual=downward_hit(x,51.5,1)
        if hit!=f"site_rear_patio_step_{index}" or abs(actual-z)>.02:
            raise AssertionError(f"Rear patio step {index} misses access: {hit} at {actual:.3f}ft")
    if any(bpy.data.objects.get(f"site_rear_ground_step_{index}") for index in range(4)):
        raise AssertionError("Obsolete direct rear-door steps remain")
    if any(bpy.data.objects.get(f"site_utility_access_step_{index}") for index in range(3,6)):
        raise AssertionError("Unsupported exterior utility steps remain")
    pier_hit,pier_y=forward_hit(11.5,52,4)
    if pier_hit!="site_rear_patio_pier_middle" or abs(pier_y-53.05)>.02:
        raise AssertionError(f"Rear patio pier line is open: {pier_hit} at {pier_y:.3f}ft")
    header_hit,header_y=forward_hit(8,52,8.3)
    if header_hit!="site_rear_patio_header" or abs(header_y-53.05)>.02:
        raise AssertionError(f"Rear patio header is open: {header_hit} at {header_y:.3f}ft")
    door_hit,door_y=forward_hit(2.25,52,0)
    if door_hit!="site_rear_utility_door_leaf" or abs(door_y-53.13)>.02:
        raise AssertionError(f"Rear utility door is missing at grade: {door_hit} at {door_y:.3f}ft")
    detached_rake_x=(DETACHED_WEST_X-.7+(DETACHED_WEST_X+DETACHED_EAST_X)/2)/2
    detached_rake_z=((8+0.5/12)+(12+1/12))/2-.08+SITE_GRADE+.16
    hit,_=forward_hit(detached_rake_x,DETACHED_FRONT_Y-1.2,detached_rake_z)
    if hit!="site_detached_roof_rake_front_left":
        raise AssertionError(f"Detached rake perimeter hit {hit}, expected site_detached_roof_rake_front_left")
    # Saved-scene probes verify A1.0 circulation remains exposed rather than
    # covered by landscape, including the south passage and Unit 2 approach.
    for x,y,label in [(40,25,"south passage"),(25,52,"courtyard connection"),(25,89,"detached entry walk"),(-1,95,"detached north walk")]:
        hit,_=downward_hit(x,y,1)
        if not hit.startswith("site_") or not ("walk" in hit or "passage" in hit):
            raise AssertionError(f"{label} is covered by {hit}")
    for walk_name in ["site_detached_walk_front","site_detached_walk_west","site_detached_walk_east","site_detached_walk_rear"]:
        walk_low,walk_high=world_bounds(walk_name)
        for obj in bpy.data.collections["SITE_LAYOUT"].all_objects:
            if not obj.name.startswith("site_landscape_zone_"): continue
            low,high=world_bounds(obj.name)
            overlap_x=min(walk_high[0],high[0])-max(walk_low[0],low[0])
            overlap_y=min(walk_high[1],high[1])-max(walk_low[1],low[1])
            if overlap_x>1e-5 and overlap_y>1e-5:
                raise AssertionError(f"{obj.name} overlaps {walk_name}")
    # An interior ray in BED4 must reach its retained floor without hitting
    # the separately owned porch roof.
    for x,y in [(1,0),(8,0),(14,0),(1,5),(8,5),(14,5)]:
        hit,z=downward_hit(x,y,18)
        if hit=="site_roof_front_porch" or z>10.2:
            raise AssertionError(f"BED4 interior ({x}, {y}) is obstructed by {hit} at {z:.3f}ft")
    porch_hit,porch_z=downward_hit(8,3.3,1)
    if porch_hit not in {"site_front_porch","layout_foyer_floor"} or abs(porch_z)>.02:
        raise AssertionError(f"Porch does not meet entry FFL: {porch_hit} at {porch_z:.3f}ft")
    for i,(y,expected_z) in enumerate([(-3.5,-.55),(-4.5,-1.1),(-5.5,-1.65),(-6.5,-2.2)]):
        step_hit,step_z=downward_hit(8,y,1)
        if step_hit!=f"site_front_step_{i}" or abs(step_z-expected_z)>.02:
            raise AssertionError(f"Front step {i} is covered: {step_hit} at {step_z:.3f}ft")
        left=4-i*.5; right=12+i*.5
        for x in (left-.2,left+.2,right-.2,right+.2):
            edge_hit,_=downward_hit(x,y,1)
            if edge_hit not in {f"site_front_step_{i}","site_ground"}:
                raise AssertionError(f"Front stair terrain gap at ({x}, {y}): {edge_hit}")
    for i,(y,z,expected) in enumerate([
        (-3.2,-.275,"site_front_porch_slab_face"),
        (-4.2,-.825,"site_front_step_0"),
        (-5.2,-1.375,"site_front_step_1"),
        (-6.2,-1.925,"site_front_step_2"),
        (-7.2,-2.475,"site_front_step_3"),
    ]):
        riser_hit,_=forward_hit(8,y,z)
        if riser_hit!=expected:
            raise AssertionError(f"Front rise {i} is open: {riser_hit}")
    walk_hit,walk_z=downward_hit(13,-7.5,1)
    if walk_hit not in {"site_front_walk","site_ground"} or abs(walk_z-(SITE_GRADE+.02))>.03:
        raise AssertionError(f"Front approach misses lower grade: {walk_hit} at {walk_z:.3f}ft")
    if any(obj.name.startswith("site_") and not ({c.name for c in obj.users_collection} & {"SITE_LAYOUT","SITE_ROOFS","SITE_LAYOUT_CAMERAS"}) for obj in bpy.data.objects):
        raise AssertionError("A site-owned object escaped its owned collections")
    export=bpy.data.collections.get("EXPORT")
    if not export: raise AssertionError("Missing preserved EXPORT collection")
    if any(obj.name.startswith("site_") for obj in export.all_objects): raise AssertionError("Site objects entered two-room EXPORT")
    print(f"Sage site check passed: {len(bpy.data.collections['SITE_LAYOUT'].all_objects)} objects; parcel {parcel_x:.3f} by {parcel_y:.3f}ft checked in native geometry")


if __name__=="__main__":
    try: main()
    except Exception as exc: print(f"ERROR: {exc}",file=sys.stderr); raise
