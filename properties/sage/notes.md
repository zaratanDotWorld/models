# Sage living and dining reconstruction notes

## Arrangement

The reconstruction targets the furniture arrangement in `photos/house/living.JPG` and `photos/house/dining.JPG`, photographed on March 23, 2023 according to their EXIF metadata.
The listing photographs preserve stronger architectural coverage but show a different furniture arrangement.
Use listing views to judge fixed walls, openings, windows, trim, paneling, wallpaper, and compatible furnishings without moving target furniture to match them.

The four initial comparison cameras are `ref_living_primary`, `ref_living_opening`, `ref_dining_primary`, and `ref_dining_cabinet`.
The first and third cameras target the personal photographs, and the other two add architectural coverage for one room each.
Listing images 03 and 05 remain supporting cross-room views for checking the shared opening and alignment.
The primary photographs report a 13-millimeter 35-millimeter-equivalent ultra-wide lens, while listing images 02 and 04 report a Canon 17-millimeter lens.
These EXIF values seed placeholder projections and do not establish final calibrated fields of view after image correction or cropping.

## Plan-supported dimensions

Sheet A2.0 of `design/floor-plans.pdf` shows the living-room interior as 16 feet 3 inches wide and 13 feet 10 inches deep.
The same sheet labels the living-room exterior depth as 14 feet 9 inches, the front window as 9 feet wide, and the side window as 4 feet 6 inches wide.
Sheet A2.0 shows the dining-room interior depth as 11 feet 10 inches and its exterior depth as 12 feet 8 inches.
The dining-room side wall has two windows labeled 3 feet 4 inches each.
The drawing crop inspected for these readings is `.local/a20-room-dimensions.png`, generated from the first PDF page at 600 DPI and excluded from Git.

The hand-drawn lower-floor sketch confirms room names and connections but supplies no dimensions.
The website prototype uses approximate bounds of 16.3 by 14.5 feet for `living` and 18 by 12.5 feet for `dining`.
Those prototype bounds are a baseline implementation reference and are not evidence about the house.

## Observed and inferred areas

The photos directly support the visible room finishes, furniture silhouettes, exterior windows, wood-trimmed shared opening, living-to-foyer opening, and dining-to-kitchen doorway.
The primary living image supports the red sofa, shelving, round rug, coffee table, metal-framed chair, upholstered armchair, leather pouf, stained-glass screen, curtains, and the visible edge of the piano.
The primary dining image supports the oak cabinet, paneling, table, benches, chandelier, curtains, and window proportions.

Furniture dimensions, exact camera poses, wall thickness where the plan does not label it, and hidden surfaces remain inferred.
The complete floor plans now constrain the adjoining room outlines, while their finishes and furnishings remain neutral.
Lighting conditions differ between the personal and listing photographs, and matching one set should not be treated as proof of the other.

## Prototype baseline

Fresh baseline screenshots are generated outputs under `renders/baseline/` and remain outside Git.
`properties/sage/baseline.json` records the capture environment, camera poses, and hashes of the website inputs that determine these two views.
They were captured on September 19, 2026 from website revision `78f419bfd31ed0b1a68a2b1a87dbefe34aa28e68` with the checkout's pre-existing uncommitted Sage prototype intact.
The relevant source SHA-256 digests were `65e9cf9994d5f1d2998ca7df48a977be0fc3de75ddba860046b6dcd88d6e9bd8` for `components/sage-tour/Scene.jsx` and `830218f6296b6e1a2bc4dc744124709c7b366675e8294c16e71129c8786c79fe` for `components/sage-tour/house.js`.
Both captures used headless Google Chrome 153.0.8010.48 on macOS with a 1440 by 900 CSS-pixel viewport and device scale factor 2.
The scene measured 1032 by 712 CSS pixels, its canvas rendered at 2064 by 1424 pixels, and element screenshot rounding produced 2064 by 1426-pixel files.
The prototype uses a Three.js `PerspectiveCamera` with a 75-degree vertical field of view in walk mode.

`prototype-living-scene-1032x712.png` uses the living-room pose `[23, 5.3, -13]` feet, yaw `3.0` radians, and pitch `-0.18` radians.
`prototype-dining-scene-1032x712.png` uses the dining-room pose `[18.2, 5.3, -17.2]` feet, yaw `1.0` radian, and the default pitch `-0.12` radians.
The two `prototype-*-1440x900.png` files retain the corresponding complete-page viewport context.
The coordinate conversion is the prototype's direct mapping from plan `[x, z]` to Three.js `[x, 5.3, -z]` in feet.

To repeat the captures, start the website checkout with `pnpm dev --port 3017`, open `http://127.0.0.1:3017/houses/sage/tour`, set the viewport to 1440 by 900, choose each room from the room selector, wait for the canvas to render, and save the full `[data-testid="sage-scene"]` element under `renders/baseline/`.
These screenshots record the current procedural model for later comparison and do not establish reconstruction accuracy.

## Reconstruction comparison notes

The saved reference cameras use the poses, vertical fields of view, source associations, and output sizes recorded in `references.json`.
The two primary cameras retain the portrait orientation and ultra-wide starting projection reported by EXIF, while the two listing cameras retain a 70-degree landscape projection.
The camera poses were adjusted against window edges, ceiling joins, the shared opening, and the dining cabinet rather than inferred from lens metadata alone.

The reconstruction uses the verified 4.9530 by 4.2164-meter living interior and 3.6068-meter dining depth from the current right-hand A2.0 plan.
The same plan crop calibrates at about 44.4 pixels per foot from the printed living spans.
Traced estimates from the plan are a 2.783-meter shared opening offset 0.991 meters from the living left face, a 0.279-meter shared wall, a 0.454-meter dining right step, and a 0.180-meter dining left inset.
The living-to-foyer opening is traced as 1.95 meters wide from 1.54 to 3.49 meters behind the living front face.
The dining-to-foyer opening is traced as 0.89 meters wide, and the kitchen doorway is traced as 0.80 meters wide at a 0.87-meter offset from the living left face.
The dining front-right and rear-right corner forms are traced separately because their plan widths differ.
The 2.7432-meter ground clear height is supported by A3.0, while furniture dimensions remain inferred from the photographs and prototype.
The complete right-hand A2.0 and A2.1 layouts now govern the adjoining room depths and circulation.

The living and dining wallpaper files are attributed generated approximations rather than observed scans.
Wood grain, patterned textiles, exterior views, glass reflections, curtain folds, and the cabinet's small contents remain simplified.
The primary arrangement follows the personal photographs.
The listing comparisons exclude their television, alternate seating, extra dining chair, and tabletop objects.

Remaining differences are grouped as follows.

- Geometry: the cabinet arches, furniture curves, curtains, and adjoining-room finishes are simplified, while hidden surfaces remain inferred.
- Arrangement: the primary furniture is retained when listing photographs show later movable furnishings.
- Materials: wallpaper color and repeat, wood grain, upholstery weave, rug wear, and stained glass are approximations.
- Lighting: the saved Cycles setup approximates daylight and the dining fixture without reproducing the photographs' exposure or exterior environment.

## Canonical two-floor layout

The right-hand A2.0 and A2.1 drawings in `design/floor-plans.pdf` govern both modeled floors.
The detailed living and dining rooms retain their measured geometry and furnishings within the complete neutral layout.
Ground architectural BED3, BED1, and BED2 map to `room-1`, `room-2`, and `room-3`.
Upper BED4 through BED7 map to `room-4` through `room-7`, while BED10, BED9, and BED8 map to `room-8`, `room-9`, and `room-10`.
The saved upper finished-floor elevation is 10 feet above ground, based on A3.0's 9-foot ground clear height and 1-foot floor assembly.
The upper clear height is 8 feet 6 inches.
The neutral inter-floor assembly fills the structural band from 9 feet 0.96 inches through 9 feet 11.04 inches, follows the asymmetric upper room and facade profiles, and leaves the A2.1 stair opening clear.
Gray dashed demolition walls and closets are omitted.
The solid linen west partition follows A2.1 while the demolished vestibule partition below it remains absent.
The staircase follows the two source footprints with an inferred count of eight risers per flight.
The rear deck follows the source-visible side and rear outline, while its outer depth remains inferred because the drawing does not print it.
The recessed front facade, two entrance door openings, and their floor thresholds are modeled without exterior entrance steps because their heights are not shown.
Rear utility-basement access is represented by three visible exterior context steps outside BED2, with inferred half-foot drops and no basement floor.
The full-house export is separate from the two-room website contract and intentionally carries no browser metadata file.
The source/model gallery at `renders/sage-house-layout/index.html` pairs the complete right-hand plan crops with labeled model plans and shows both front and rear cutaways.
