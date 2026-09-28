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
    close(detached_low[1]/FT-house_rear,HOUSE_TO_UNIT,.15,"saved house to detached separation")
    close(garage_low[1]/FT-(detached_low[1]/FT+DETACHED_ALONG),UNIT_TO_GARAGE,.03,"saved detached to garage separation")
    close(ground_high[1]/FT-garage_high[1]/FT,ALLEY_SETBACK,.03,"saved garage alley setback")
    close(detached_low[0]/FT-PROPERTY_WEST_X,5,.03,"detached north setback")
    close(garage_low[0]/FT-PROPERTY_WEST_X,2,.03,"garage north setback")
    for name in ["site_roof_main_complex","site_roof_front_porch","site_roof_rear_pitch_break","site_detached_roof","site_garage_roof","site_rear_exterior_stair"]:
        if name not in bpy.data.objects: raise AssertionError(f"Missing {name}")
    expected_doors={
        "site_frame_g_rear_2_leaf":(98/37.046,7),
        "site_frame_g_foyer_entry_0_leaf":(104/37.046,7),
        "site_frame_g_foyer_entry_1_leaf":(105/37.046,7),
        "site_frame_u_rear_1_leaf":(110/37,7),
        "site_detached_south_entry_frame_0_leaf":(3,6+8/12),
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
        for index in range(0,15,3):
            post_low,post_high=world_bounds(f"site_rear_stair_lower_post_{y}_{index}")
            if post_high[2]-post_low[2]<1.5*FT:
                raise AssertionError(f"Rear stair rail post {y}/{index} does not connect tread and rail")
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
    # Saved-scene probes verify A1.0 circulation remains exposed rather than
    # covered by landscape, including the south passage and Unit 2 approach.
    for x,y,label in [(40,25,"south passage"),(25,52,"courtyard connection"),(25,89,"detached entry walk"),(-1,95,"detached north walk")]:
        hit,_=downward_hit(x,y,1)
        if not hit.startswith("site_") or not ("walk" in hit or "passage" in hit):
            raise AssertionError(f"{label} is covered by {hit}")
    walk_low,walk_high=world_bounds("site_detached_walk")
    for obj in bpy.data.collections["SITE_LAYOUT"].all_objects:
        if not obj.name.startswith("site_landscape_zone_"): continue
        low,high=world_bounds(obj.name)
        overlap_x=min(walk_high[0],high[0])-max(walk_low[0],low[0])
        overlap_y=min(walk_high[1],high[1])-max(walk_low[1],low[1])
        if overlap_x>1e-5 and overlap_y>1e-5:
            raise AssertionError(f"{obj.name} overlaps the detached perimeter walk")
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
            if edge_hit not in {f"site_front_step_{i}","site_front_step_bank_left","site_front_step_bank_right"}:
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
    if walk_hit not in {"site_front_walk","site_ground"} or abs(walk_z+2.75)>.02:
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
