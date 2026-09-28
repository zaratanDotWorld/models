"""Canonical Sage layout transcribed from the right-hand A2.0/A2.1 drawings."""

GROUND_ORIGIN = (3344.2, 2646.6)
GROUND_SCALE = (37.046, 37.157)
UPPER_ORIGIN = (3364.75, 2622.5)
UPPER_SCALE = (37.0, 37.0)
UPPER_Z = 10.0
GROUND_HEIGHT = 9.0
UPPER_HEIGHT = 8.5


def point(floor, absolute_x, absolute_y):
    origin = GROUND_ORIGIN if floor == "ground" else UPPER_ORIGIN
    scale = GROUND_SCALE if floor == "ground" else UPPER_SCALE
    return ((absolute_x - origin[0]) / scale[0], (origin[1] - absolute_y) / scale[1])


def crop_point(floor, crop_origin, x, y):
    return point(floor, crop_origin[0] + x, crop_origin[1] + y)


def horizontal(floor, crop_origin, wall_id, y, x1, x2, apertures=(), thickness=5 / 12):
    start = crop_point(floor, crop_origin, x1, y)
    end = crop_point(floor, crop_origin, x2, y)
    sx = GROUND_SCALE[0] if floor == "ground" else UPPER_SCALE[0]
    return {"id": wall_id, "start": start, "end": end, "thickness": thickness,
            "apertures": [{"kind": kind, "start": (a - x1) / sx, "end": (b - x1) / sx, "bottom": bottom, "top": top} for kind, a, b, bottom, top in apertures]}


def vertical(floor, crop_origin, wall_id, x, y1, y2, apertures=(), thickness=5 / 12):
    start = crop_point(floor, crop_origin, x, y1)
    end = crop_point(floor, crop_origin, x, y2)
    sy = GROUND_SCALE[1] if floor == "ground" else UPPER_SCALE[1]
    return {"id": wall_id, "start": start, "end": end, "thickness": thickness,
            "apertures": [{"kind": kind, "start": (a - y1) / sy, "end": (b - y1) / sy, "bottom": bottom, "top": top} for kind, a, b, bottom, top in apertures]}


GR = (3250, 780)
GF = (3250, 1820)
UR = (3250, 770)
UF = (3250, 1840)
GE = (4480, 780)

# Interior floor faces; printed clear spans take precedence over sub-pixel trace differences.
GROUND_ROOMS = {
    "foyer": [crop_point("ground", GF, x, y) for x, y in [(98,89),(680,89),(680,750),(584,750),(584,712),(538,712),(538,704),(234,704),(234,712),(186,712),(186,750),(98,750)]],
    "room-1": [(0.10,20.31),(15.60,20.31),(15.60,31.48),(0.10,31.48)],
    "bath-lower-front": [crop_point("ground", GR, x, y) for x,y in [(98,407),(269,407),(269,584),(290,584),(290,684),(98,684)]],
    "pantry": [crop_point("ground", GR, x, y) for x,y in [(298,407),(595,407),(595,684),(298,684)]],
    "room-3": [crop_point("ground", GR, x, y) for x,y in [(98,47),(394,47),(394,399),(98,399)]],
    "bath-lower-back": [crop_point("ground", GR, x, y) for x,y in [(410,47),(612,47),(612,399),(410,399)]],
    "laundry": [crop_point("ground", GR, x, y) for x,y in [(633,47),(817,47),(817,294),(633,294)]],
    "rear-hall": [crop_point("ground", GR, x, y) for x,y in [(628,294),(817,294),(817,392),(744,392),(744,407),(752,407),(752,602),(680,602),(680,692),(611,692),(611,407),(644,407),(644,392),(628,392)]],
    "room-2": [crop_point("ground", GR, x, y) for x,y in [(833,47),(1289,47),(1289,399),(833,399)]],
    "kitchen": [crop_point("ground", GR, x, y) for x,y in [(768,407),(1289,407),(1289,848),(680,848),(680,602),(752,602),(752,473),(768,473)]],
}

UPPER_ROOMS = {
    "room-4": [crop_point("upper", UF,x,y) for x,y in [(117,334),(690,334),(690,791),(117,791)]],
    "room-5": [crop_point("upper", UF,x,y) for x,y in [(698,334),(848,334),(848,404),(1315,404),(1315,827),(698,827)]],
    "landing": [crop_point("upper", UF,x,y) for x,y in [(254,184),(525,184),(525,63),(690,63),(690,325),(269,325),(269,199),(254,199)]],
    "room-6": [crop_point("upper", UF,x,y) for x,y in [(848,60),(1315,60),(1315,404),(848,404)]],
    "linen": [crop_point("upper", UF,x,y) for x,y in [(698,60),(848,60),(848,156),(698,156)]],
    "vestibule": [crop_point("upper", UF,x,y) for x,y in [(690,164),(840,164),(840,326),(690,326)]],
    "room-7": [crop_point("upper", UR,x,y) for x,y in [(698,868),(893,868),(893,698),(1315,698),(1315,1122),(698,1122)]],
    "bath-upper-middle": [crop_point("upper", UR,x,y) for x,y in [(698,514),(893,514),(893,868),(698,868)]],
    "room-10": [crop_point("upper", UR,x,y) for x,y in [(893,388),(1315,388),(1315,698),(893,698)]],
    "room-9": [crop_point("upper", UR,x,y) for x,y in [(109,388),(539,388),(539,758),(109,758)]],
    "room-8": [crop_point("upper", UR,x,y) for x,y in [(109,758),(539,758),(539,1002),(527,1002),(527,1125),(109,1125)]],
    "hall": [crop_point("upper", UR,x,y) for x,y in [(539,574),(698,574),(698,1125),(527,1125),(527,965),(539,965)]],
    "rear-upper-hall": [crop_point("upper", UR,x,y) for x,y in [(539,246),(698,246),(698,388),(893,388),(893,514),(698,514),(698,574),(539,574)]],
    "bath-upper-back": [crop_point("upper", UR,x,y) for x,y in [(322,36),(539,36),(539,388),(322,388)]],
    "library": [crop_point("upper", UR,x,y) for x,y in [(539,36),(1247,36),(1247,388),(698,388),(698,246),(539,246)]],
    # A2.1 fixes the 5ft9in side deck beside Bath 208.  Its 25ft5in rear
    # dimension line was previously misread as a full-width deck edge.
    # Photos 18/19/21/26 and deck.JPG support an approximately 19ft by 8ft
    # rear platform, with its outer post line short of existing window 207.3.
    "deck": [(-.1554054054054054,39.58108108108108),(5.601351351351352,39.58108108108108),(5.601351351351352,49.310810810810814),(19,49.310810810810814),(19,57.310810810810814),(-.1554054054054054,57.310810810810814)],
}

STAIR_OPENING = [crop_point("upper", UF,x,y) for x,y in [(117,63),(525,63),(525,184),(254,184),(254,326),(117,326)]]

GROUND_WALLS = [
    vertical("ground", GR,"g_west",90,39,1798,[("window",195,343,3,7),("window",546,644,3,7),("window",824,991,3,7),("window",1460,1626,3,7)]),
    horizontal("ground",GR,"g_rear",39,90,1297,[("door",284,382,0,7),("window",507,581,3,7),("door",633,731,0,7),("window",957,1191,3,7)]),
    vertical("ground",GR,"g_east_rear",1297,39,856,[("window",174,271,3,7),("window",487,598,3,7),("window",615,727,3,7)]),
    vertical("ground",GR,"g_bed2_bath1",402,39,399), vertical("ground",GR,"g_bath1_laundry",620,39,399,[("door",294,392,0,7)]),
    vertical("ground",GR,"g_laundry_bed1",825,39,399,[("door",294,382,0,7)]),
    horizontal("ground",GR,"g_rear_rooms_south",399,98,1289,[("door",304,392,0,7),("opening",644,744,0,9)]),
    vertical("ground",GR,"g_bath2_east_upper",277,407,584,[("door",462,548,0,7)]),
    horizontal("ground",GR,"g_bath2_jog",584,277,298), vertical("ground",GR,"g_bath2_east_lower",298,584,692),
    vertical("ground",GR,"g_hall_east",603,407,684,[("opening",493,587,0,9)]),
    horizontal("ground",GR,"g_bed3_north",692,98,680,[("door",384,477,0,7)]),
    horizontal("ground",GF,"g_bed3_south",89,98,673,(),thickness=11/12),
    vertical("ground",GR,"g_bed3_east",673,700,861),
    vertical("ground",GR,"g_pot_return",760,407,473), vertical("ground",GR,"g_fridge_west",680,610,848),
    vertical("ground",GR,"g_fridge_east",780,610,848), horizontal("ground",GR,"g_fridge_north",610,680,780),
    vertical("ground",GF,"g_coat_west",242,234,375), vertical("ground",GF,"g_coat_east",365,234,375,[("door",263,336,0,7)]),
    horizontal("ground",GF,"g_coat_north",234,242,365), horizontal("ground",GF,"g_coat_south",375,242,365),
    horizontal("ground",GF,"g_foyer_left_outer",758,90,186), vertical("ground",GF,"g_foyer_left_step",186,704,758), horizontal("ground",GF,"g_foyer_left_inner",704,186,234),
    horizontal("ground",GF,"g_foyer_entry",704,234,538,[("door",234,338,0,7),("door",433,538,0,7)]),
    horizontal("ground",GF,"g_foyer_right_inner",704,538,584), vertical("ground",GF,"g_foyer_right_step",584,704,758), horizontal("ground",GF,"g_foyer_right_outer",758,584,680),
]

UPPER_WALLS = [
    vertical("upper",UR,"u_west_rear",109,388,1070,[("window",839,950,3,7)]),
    vertical("upper",UF,"u_west_front",109,0,791,[("window",79,164,3,7),("window",190,276,3,7),("window",353,464,3,7)]),
    horizontal("upper",UR,"u_bed9_north",388,109,322,[("door",124,234,0,7)]), vertical("upper",UR,"u_bath3_west",322,28,388,[("window",148,258,3,7)]),
    # A3.1 marks 207.2 as a new window, but the owner confirmed it was not built;
    # photos 18 and 21 show the finished blank wall.  Retain existing 207.3.
    horizontal("upper",UR,"u_rear",28,322,1247,[("window",343,454,3,7),("door",633,743,0,7),("window",899,1009,3,7)]),
    vertical("upper",UR,"u_library_east",1247,28,388,[("window",157,269,3,7)]), horizontal("upper",UR,"u_rear_shoulder",388,1247,1315),
    vertical("upper",UR,"u_east_rear",1315,388,1098,[("window",455,653,3,7),("window",730,830,3,7),("window",954,1053,3,7)]),
    vertical("upper",UF,"u_east_front",1315,28,827,[("window",69,167,3,7),("window",426,525,3,7)]),
    horizontal("upper",UF,"u_bed4_front",791,109,698,[("window",205,314,3,7),("window",494,604,3,7)]),
    horizontal("upper",UF,"u_bed5_front",827,698,1315,[("window",724,817,3,7),("window",869,1141,3,7)]),
    vertical("upper",UR,"u_west_internal",539,36,1002,[("door",257,354,0,7),("door",476,574,0,7),("door",867,965,0,7)]),
    horizontal("upper",UR,"u_bed10_inset",1002,527,539), vertical("upper",UR,"u_bed10_east_lower",527,1002,1125),
    horizontal("upper",UR,"u_library_entry_north",246,539,698,[("opening",553,684,0,8.5)]), vertical("upper",UR,"u_library_entry_east",698,246,388),
    horizontal("upper",UR,"u_library_south",388,698,1247), horizontal("upper",UR,"u_bed9_bed10",758,109,539),
    vertical("upper",UR,"u_bed8_west",893,388,868,[("door",395,499,0,7)]), horizontal("upper",UR,"u_bed8_bed7",698,893,1315),
    horizontal("upper",UR,"u_bath4_north",514,698,893,[("door",714,811,0,7)]), horizontal("upper",UR,"u_bath4_south",868,698,893),
    vertical("upper",UR,"u_bath4_bed7_west",698,514,1098,[("door",1002,1098,0,7)]),
    horizontal("upper",UF,"u_bed10_stair",55,109,547), horizontal("upper",UF,"u_bed7_linen_bed6",52,698,1315),
    vertical("upper",UF,"u_linen_west",698,52,156),
    horizontal("upper",UF,"u_linen_south",156,698,848,[("opening",724,822,0,8.5)]),
    vertical("upper",UF,"u_bed6_west",848,60,404,[("door",196,294,0,7)]), horizontal("upper",UF,"u_bed6_bed5",404,848,1315),
    horizontal("upper",UF,"u_bed4_north",334,109,698,[("door",540,638,0,7)]), horizontal("upper",UF,"u_bed5_neck_north",334,698,848,[("door",724,822,0,7)]),
    vertical("upper",UF,"u_bed4_bed5",698,334,827),
]

# Exterior window heights transcribed from A3.0/A3.1 and A0.5.  The accepted
# plan trace continues to govern horizontal positions; the neutral shell's old
# blanket 3ft sill / 7ft head assumption does not.
_WINDOW_SCHEDULE = {
    "100.1": (5, 7), "103.1": (3.5, 7), "103.2": (3.5, 7), "104.1": (4+2/12, 7),
    "104.2": (4.5, 7), "106.1": (3, 7), "107.1": (4+2/12, 7), "107.2": (3, 7),
    "108.1": (2+8/12, 7), "109.1": (5, 7),
    "200.1": (4+4/12, 6), "200.2": (4+4/12, 6),
    "201.1": (4.5, 6+8/12), "201.2": (4.5, 6+8/12), "201.3": (4.5, 6+8/12),
    "203.1": (2, 6+8/12), "203.2": (4.5, 6+8/12), "203.3": (4.5, 6+8/12),
    "204.1": (4.5, 6+8/12), "205.1": (4.5, 6+8/12), "205.2": (4.5, 6+8/12),
    "206.1": (4.5, 6+8/12), "207.1": (4, 6+8/12), "207.2": (3+10/12, 6+8/12),
    "207.3": (3+10/12, 6+8/12), "208.1": (3+4/12, 6+8/12),
    "208.2": (3+10/12, 6+8/12), "209.1": (4.5, 6+8/12), "210.1": (4.5, 6+8/12),
}
_EXTERIOR_MARKS = {
    "g_west": ("107.2","108.1","109.1","100.1"),
    "g_rear": ("107.1","106.1",None,"104.2"),
    "g_east_rear": ("104.1","103.2","103.1"),
    "u_west_rear": ("210.1",), "u_west_front": ("200.1","200.2","201.1"),
    "u_bed9_north": ("209.1",), "u_bath3_west": ("208.2",),
    "u_rear": ("208.1",None,"207.3"), "u_library_east": ("207.1",),
    "u_east_rear": ("206.1","205.2","205.1"), "u_east_front": ("204.1","203.3"),
    "u_bed4_front": ("201.2","201.3"), "u_bed5_front": ("203.1","203.2"),
}
for _wall in GROUND_WALLS + UPPER_WALLS:
    for _opening, _mark in zip(_wall.get("apertures", ()), _EXTERIOR_MARKS.get(_wall["id"], ())):
        if not _mark:
            continue
        _height, _head = _WINDOW_SCHEDULE[_mark]
        if _mark in {"200.1", "200.2"}:
            # A3.1 places these stair windows from 6ft8in to 11ft above the
            # main FFL; their A0.5 head is referenced to the 5ft stair landing.
            _opening.update(kind="window", bottom=-3-4/12, top=1.0, source_mark=_mark, datum="stair landing at 5ft")
        else:
            _opening.update(kind="window", bottom=_head-_height, top=_head, source_mark=_mark)

# The two 200-series stair windows cross the ground wall and inter-floor band.
# Their plan positions come from u_west_front; these lower segments use the
# same world Y extents expressed as offsets from g_west's rear-to-front start.
_ground_west = next(_wall for _wall in GROUND_WALLS if _wall["id"] == "g_west")
_upper_west = next(_wall for _wall in UPPER_WALLS if _wall["id"] == "u_west_front")
for _opening in _upper_west["apertures"][:2]:
    _world_y1 = _upper_west["start"][1] - _opening["start"]
    _world_y2 = _upper_west["start"][1] - _opening["end"]
    _ground_west["apertures"].append({
        "kind":"window", "start":_ground_west["start"][1]-_world_y1,
        "end":_ground_west["start"][1]-_world_y2, "bottom":6+8/12,
        "top":GROUND_HEIGHT, "source_mark":_opening["source_mark"], "datum":"stair landing at 5ft",
    })
