"""Replace only HOUSE_LAYOUT architecture and layout cameras, then save the loaded master."""

import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sage_house_builder import empty, owned_collection, prism, wall_piece, wall_with_apertures
from sage_house_layout import GROUND_HEIGHT, GROUND_ROOMS, GROUND_WALLS, STAIR_OPENING, UPPER_HEIGHT, UPPER_ROOMS, UPPER_WALLS, UPPER_Z, crop_point, GF, GR, UF, UR
from sage_scene import DINING_DEPTH, DINING_LEFT_INSET, FRONT_WALL, FT, LIVING_DEPTH, LIVING_X, SHARED_WALL

OWNED = "HOUSE_LAYOUT"
CAMERAS = "HOUSE_LAYOUT_CAMERAS"
EXTERIOR_UPPER_WALLS = {
    "u_west_rear", "u_west_front", "u_bed9_north", "u_bath3_west", "u_rear",
    "u_library_east", "u_rear_shoulder", "u_east_rear", "u_east_front",
    "u_bed4_front", "u_bed5_front", "u_bed10_inset", "u_bed10_east_lower",
}


def material(name, color):
    value = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    value.diffuse_color = (*color, 1)
    return value


def thresholds(collection, walls, elevation, parent, material):
    """Fill each complete scheduled door/opening across only its wall thickness."""
    for spec in walls:
        start = Vector(spec["start"])
        direction = Vector(spec["end"]) - start
        direction.normalize()
        normal = Vector((-direction.y, direction.x))
        half = spec.get("thickness", 5/12) / 2
        for index, opening in enumerate(spec.get("apertures", [])):
            if opening["kind"] == "window":
                continue
            a = start + direction * opening["start"]
            b = start + direction * opening["end"]
            outline = [a-normal*half,b-normal*half,b+normal*half,a+normal*half]
            prism(collection,f"layout_threshold_{spec['id']}_{index}",[tuple(point) for point in outline],elevation-.08,elevation-.01,parent,material)


def detailed_room_thresholds(collection, ground, material):
    """Join the three detailed-room apertures to the new adjoining floor faces."""
    foyer_east = max(x for x, _ in GROUND_ROOMS["foyer"])
    living_x = LIVING_X / FT
    living_y1 = (FRONT_WALL + 1.54) / FT
    living_y2 = (FRONT_WALL + 3.49) / FT
    prism(collection,"layout_threshold_living_foyer",[(foyer_east,living_y1),(living_x,living_y1),(living_x,living_y2),(foyer_east,living_y2)],-.08,-.01,ground,material)
    dining_front = (FRONT_WALL + LIVING_DEPTH + SHARED_WALL) / FT
    dining_x = (LIVING_X + DINING_LEFT_INSET) / FT
    dining_y1 = dining_front + .29 / FT
    dining_y2 = dining_front + 1.18 / FT
    prism(collection,"layout_threshold_dining_foyer",[(foyer_east,dining_y1),(dining_x,dining_y1),(dining_x,dining_y2),(foyer_east,dining_y2)],-.08,-.01,ground,material)
    dining_back = (FRONT_WALL + LIVING_DEPTH + SHARED_WALL + DINING_DEPTH) / FT
    kitchen_front = min(y for _, y in GROUND_ROOMS["kitchen"])
    door_x1 = (LIVING_X + .87) / FT
    door_x2 = (LIVING_X + 1.67) / FT
    prism(collection,"layout_threshold_dining_kitchen",[(door_x1,dining_back),(door_x2,dining_back),(door_x2,kitchen_front),(door_x1,kitchen_front)],-.08,-.01,ground,material)


def floor_assembly(collection, upper, material):
    """Fill the one-foot A3.0 floor band while retaining the A2.1 stair opening."""
    bottom = GROUND_HEIGHT + .08
    top = UPPER_Z - .08
    for name, outline in UPPER_ROOMS.items():
        if name != "deck":
            prism(collection,f"layout_floor_assembly_{name}",outline,bottom,top,upper,material)
    for spec in UPPER_WALLS:
        if spec["id"] in EXTERIOR_UPPER_WALLS:
            wall_piece(collection,f"layout_floor_assembly_{spec['id']}",spec["start"],spec["end"],bottom,top,spec.get("thickness",5/12),upper,material)


def carve_stair_window_band(collection):
    """Continue A3.1 windows 200.1/200.2 through the inter-floor assembly."""
    wall=next(spec for spec in UPPER_WALLS if spec["id"]=="u_west_front")
    targets=[obj for obj in collection.all_objects if obj.type=="MESH" and obj.name.startswith("layout_floor_assembly_")]
    for index,opening in enumerate(wall["apertures"][:2]):
        y1=wall["start"][1]-opening["start"]; y2=wall["start"][1]-opening["end"]
        bpy.ops.mesh.primitive_cube_add(location=(-.15*FT,(y1+y2)*FT/2,9.5*FT))
        cutter=bpy.context.object; cutter.name=f"tmp_stair_window_band_{index}"; cutter.scale=(1.5*FT,abs(y2-y1)*FT/2,0.6*FT)
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        for obj in targets:
            corners=[obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
            if max(point.x for point in corners)<-1.65*FT or min(point.x for point in corners)>1.35*FT or max(point.y for point in corners)<min(y1,y2)*FT or min(point.y for point in corners)>max(y1,y2)*FT:
                continue
            modifier=obj.modifiers.new(f"stair_window_{index}","BOOLEAN"); modifier.operation="DIFFERENCE"; modifier.solver="EXACT"; modifier.object=cutter
            bpy.context.view_layer.objects.active=obj
            try: bpy.ops.object.modifier_apply(modifier=modifier.name)
            except RuntimeError: obj.modifiers.remove(modifier)
        bpy.data.objects.remove(cutter,do_unlink=True)


def layout_camera(collection, name, location, target, ortho_scale=None):
    data = bpy.data.cameras.new(name)
    camera = bpy.data.objects.new(name, data)
    collection.objects.link(camera)
    camera.location = tuple(value * .3048 for value in location)
    camera.rotation_euler = (Vector(tuple(value * .3048 for value in target)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    if ortho_scale:
        data.type = "ORTHO"
        data.ortho_scale = ortho_scale
    return camera


def room(collection, floor, name, outline, elevation, height, floor_material, ceiling_material, ceiling=True):
    node = empty(collection, name, floor)
    node["source"] = "floor-plans.pdf right-hand A2.0/A2.1"
    prism(collection, f"layout_{name}_floor", outline, elevation - .08, elevation, node, floor_material)
    if ceiling:
        ceiling_obj = prism(collection, f"layout_{name}_ceiling", outline, elevation + height, elevation + height + .08, node, ceiling_material)
        ceiling_obj["ceiling"] = True
    return node


def stairs(collection, ground, upper, wood):
    # Two flights follow the A2.0 rectangles; the second arrives at the A2.1 L-shaped opening.
    lower = [crop_point("ground", GF, x, y) for x,y in [(98,227),(235,227),(235,464),(98,464)]]
    landing = [crop_point("ground", GF, x, y) for x,y in [(98,106),(250,106),(250,227),(98,227)]]
    upper_run = [crop_point("ground", GF, x, y) for x,y in [(250,106),(508,106),(508,227),(250,227)]]
    for index in range(8):
        y0=lower[3][1]+(lower[0][1]-lower[3][1])*index/8; y1=lower[3][1]+(lower[0][1]-lower[3][1])*(index+1)/8
        prism(collection,f"layout_stair_lower_{index:02}",[(lower[0][0],y0),(lower[1][0],y0),(lower[1][0],y1),(lower[0][0],y1)],index*5/8,(index+1)*5/8,ground,wood)
    prism(collection,"layout_stair_turn",landing,4.92,5.0,ground,wood)
    for index in range(8):
        x0=upper_run[0][0]+(upper_run[1][0]-upper_run[0][0])*index/8; x1=upper_run[0][0]+(upper_run[1][0]-upper_run[0][0])*(index+1)/8
        prism(collection,f"layout_stair_upper_{index:02}",[(x0,upper_run[0][1]),(x1,upper_run[0][1]),(x1,upper_run[2][1]),(x0,upper_run[2][1])],5+index*5/8,5+(index+1)*5/8,ground,wood)
    # 42-inch guard follows the open L edge without crossing the arrival.
    guard_height=3.5
    for index,(a,b) in enumerate([(STAIR_OPENING[2],STAIR_OPENING[3]),(STAIR_OPENING[3],STAIR_OPENING[4])]):
        wall_piece(collection,f"layout_stair_guard_{index}",a,b,UPPER_Z,UPPER_Z+guard_height,.12,upper,wood)


def deck_guard(collection, deck, upper, wood):
    """Build the photo-supported guard around the side and inferred rear platform."""
    outer_y=deck[4][1]
    segments=[("outer_x",deck[3],deck[4]),("outer_right",deck[4],(18,outer_y)),("outer_left",(14,outer_y),deck[5]),("side",deck[5],deck[0])]
    for index,a,b in segments:
        direction=Vector(b)-Vector(a)
        length=direction.length
        direction.normalize()
        for suffix,z1,z2 in [("lower",10.45,10.72),("lower_middle",11.35,11.62),("upper_middle",12.25,12.52),("top",13.15,13.5)]:
            rail=wall_piece(collection,f"layout_deck_guard_{index}_{suffix}",a,b,z1,z2,.18,upper,wood)
            rail["source"]="A2.1 side deck; rear platform inferred from photos 18, 19, 21, 26 and deck.JPG"
        count=max(2,round(length/5))
        for post_index in range(count+1):
            point=Vector(a)+direction*(length*post_index/count)
            wall_piece(collection,f"layout_deck_guard_{index}_post_{post_index}",point-direction*.11,point+direction*.11,UPPER_Z,UPPER_Z+3.5,.28,upper,wood)


def main():
    if not bpy.data.filepath:
        raise RuntimeError("Load the saved master before applying the house layout")
    export = bpy.data.collections.get("EXPORT")
    authoring = bpy.data.collections.get("AUTHORING")
    if not export or not authoring:
        raise RuntimeError("Detailed master is missing EXPORT or AUTHORING")
    collection = owned_collection(OWNED)
    camera_collection = owned_collection(CAMERAS, authoring)
    ground = bpy.data.objects["ground_floor"]
    upper = empty(collection,"upper_floor")
    upper["floor_elevation_m"] = UPPER_Z * .3048
    upper["source_height"] = "A3.0: 9ft ground clear + 1ft floor assembly"
    floor_material=material("layout_floor",(.34,.29,.23)); wall_material=material("layout_wall",(.76,.74,.69)); wood=material("layout_wood",(.25,.13,.06)); deck_wood=material("main_house_deck_wood",(.38,.10,.055))
    for name,outline in GROUND_ROOMS.items(): room(collection,ground,name,outline,0,GROUND_HEIGHT,floor_material,wall_material,ceiling=name != "foyer")
    for name,outline in UPPER_ROOMS.items(): room(collection,upper,name,outline,UPPER_Z,UPPER_HEIGHT,floor_material,wall_material,ceiling=name != "deck")
    floor_assembly(collection,upper,wall_material)
    # Foyer ceiling pieces leave the full stairwell open.
    stair_front=crop_point("ground",GF,98,464)[1]; stair_rear=crop_point("ground",GF,98,106)[1]; stair_right=crop_point("ground",GF,508,106)[0]
    foyer_node=bpy.data.objects["foyer"]
    for label,outline in [
        ("front",[(.10,crop_point("ground",GF,98,750)[1]),(16,crop_point("ground",GF,98,750)[1]),(16,stair_front),(.10,stair_front)]),
        ("rear",[(.10,stair_rear),(16,stair_rear),(16,20.31),(.10,20.31)]),
        ("east",[(stair_right,stair_front),(16,stair_front),(16,stair_rear),(stair_right,stair_rear)]),
    ]:
        obj=prism(collection,f"layout_foyer_ceiling_{label}",outline,GROUND_HEIGHT,GROUND_HEIGHT+.08,foyer_node,wall_material); obj["ceiling"]=True
    for spec in GROUND_WALLS:
        wall_with_apertures(collection,spec,0,GROUND_HEIGHT,ground,wall_material,spec.get("thickness",5/12))
    for spec in UPPER_WALLS:
        wall_with_apertures(collection,spec,UPPER_Z,UPPER_HEIGHT,upper,wall_material,spec.get("thickness",5/12))
    thresholds(collection,GROUND_WALLS,0,ground,floor_material)
    thresholds(collection,UPPER_WALLS,UPPER_Z,upper,floor_material)
    detailed_room_thresholds(collection,ground,floor_material)
    stairs(collection,ground,upper,wood)
    utility = empty(collection,"utility-basement-access",ground)
    utility["source_center_ft"] = crop_point("ground",GR,170,-40)
    utility["context_only"] = "Rear access indication only; no basement floor modeled"
    utility["step_heights"] = "inferred because the floor plan gives no exterior elevation"
    for index,(near,far) in enumerate([(31,-16),(-16,-63),(-63,-110)]):
        a=crop_point("ground",GR,98,near); b=crop_point("ground",GR,243,far)
        top=-index*.5
        prism(collection,f"layout_utility_access_step_{index}",[(a[0],a[1]),(b[0],a[1]),(b[0],b[1]),(a[0],b[1])],top-.16,top,utility,wood)
    # Rear and side deck guard; deck floor itself is the `deck` room polygon.
    deck=UPPER_ROOMS["deck"]
    deck_floor=bpy.data.objects["layout_deck_floor"]
    deck_floor.data.materials.clear(); deck_floor.data.materials.append(deck_wood)
    deck_guard(collection,deck,upper,deck_wood)
    carve_stair_window_band(collection)
    for obj in bpy.data.objects:
        if obj.name.startswith("C_kitchen_context_"):
            obj.hide_render=True; obj.hide_viewport=True
    center = ((-.358+32.681)/2,24.4,0)
    layout_camera(camera_collection,"layout_ground_plan",(center[0],center[1],55),center,17.4)
    layout_camera(camera_collection,"layout_upper_plan",(center[0],center[1],55),(center[0],center[1],UPPER_Z),17.4)
    layout_camera(camera_collection,"layout_house_axon",(58,-39,52),(center[0],center[1],9))
    bpy.context.scene["house_layout_source"]="design/floor-plans.pdf A2.0/A2.1 right-hand drawings"
    bpy.context.scene["house_layout_ownership"]="HOUSE_LAYOUT and HOUSE_LAYOUT_CAMERAS; C_kitchen_context_* visibility"
    bpy.context.scene["house_layout_revision"]=1
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    print(f"Updated whole-house layout in {bpy.data.filepath}")

if __name__ == "__main__":
    try: main()
    except Exception as exc:
        print(f"ERROR: {exc}",file=sys.stderr); raise
