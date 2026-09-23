# Sage living and dining reconstruction

Status: active.

Build the first complete reconstruction workflow around Sage House's connected living and dining rooms.
The result is an editable Blender scene, comparisons against the existing photographs, and a working two-room preview in the Zaratan website.
This tests whether the approach produces a recognizable improvement over the current procedural Three.js model before extending it to the house.

See the [implementation plan](plan.md), [product specification](../../spec/product.md), and [architecture](../../spec/arch.md).

## Current and proposed behavior

The website's local `components/sage-tour/` prototype constructs the house in JavaScript, including approximate furnishings and materials.
It provides useful room layout and navigation, but its appearance falls short of a faithful reconstruction.
The models repository currently contains documentation only.

Blender will own the detailed scene and its cameras, geometry, materials, and lighting.
Python scripts will support targeted authoring, rendering, checking, and export.
The website will load the exported scene through Three.js rather than reconstruct these two rooms from measurements in JavaScript.
The existing whole-house tour remains available as the comparison baseline.

## Scope

Include the two rooms' shared opening, walls, floors, ceilings, windows, trim, doors visible from the rooms, substantial furnishings, and distinctive decoration.
Include enough adjacent doorway context to make the selected interior views coherent, with unobserved adjoining space identified as an approximation.
This feature does not reconstruct the foyer, kitchen, other rooms, exterior, or garden.

Use only the existing still photographs, plans, and owner corrections.
Additional capture, a photogrammetry or neural reconstruction pipeline, unrestricted walking with collision detection, a separate viewer application, and deployment are outside this feature.
The browser preview is a local review deliverable; publishing an applicant tour is later work.

## References and appearance

Create `properties/sage/references.json` with paths relative to `SAGE_REFERENCE_ROOT`.
Each selected reference records its room IDs, purpose, represented arrangement, and relevant observations.
Associate comparison photographs with named Blender reference cameras.
Keep source photographs outside Git and out of the exported scene.

| Reference | Role |
|---|---|
| `photos/house/living.JPG` | Primary living-room appearance and furniture arrangement |
| `photos/house/dining.JPG` | Primary dining-room appearance and furniture arrangement |
| `photos/top-360/215-N-Ave-56/01-IMG_7901.jpg` through `05-IMG_7912.jpg` | Additional architectural views; individual filenames are enumerated in the index |
| `photos/floorplan/fplan-sketch-lower.jpg` | Owner-confirmed layout and connections |
| `design/floor-plans.pdf`, sheets A2.0 and A2.1 | Dimensions and architectural context |

The personal and listing photos show different furniture arrangements.
Represent the primary photographs' arrangement, and use listing views to resolve fixed architecture and compatible details.
Record exceptions beside each comparison instead of moving furniture to make every photograph appear to agree.
These appearance targets are a selected documented arrangement, not a claim about the house's current state.

Use at least four comparison cameras: one for each primary photograph and at least one additional useful view of each room.
Select the supporting views during reference inspection, retaining their original resolution.
Match perspective against wall intersections, window and door edges, and plan dimensions before refining furniture.
Use Blender's camera controls and image backgrounds initially; do not build a camera-calibration solver.

The living room's recognizable details include the red sofa, willow-and-bird wallpaper, wood trim, record shelving, rug, coffee table, armchair, leather pouf, curtains, and visible stained glass.
The dining room's include the wood paneling and glazed cabinet, patterned wallpaper, table and benches, chandelier, curtains, and window proportions.
Model visible silhouettes, placement, and finish before small incidental objects.
Represent patterns with surface textures where useful, not flat room photographs that only work from one viewpoint.
Record source crops and edits for derived textures; label generated or inferred details as approximations.

## Authoring and recoverable assets

Start with Blender 4.5.14 LTS and its bundled Python on Apple Silicon.
The [4.5 release documentation](https://www.blender.org/releases/4-5/) identifies the supported LTS series and available builds.
Document installation and executable selection through `BLENDER_BIN`; Blender is not currently installed in the inspected checkout's environment.

Save the authoritative scene at `properties/sage/sage.blend` and required derived textures under `properties/sage/textures/` with relative paths.
Track the scene and derived texture binaries with Git LFS; track scripts, JSON, and Markdown in ordinary Git.
Git LFS needs local setup; it stores [versioned pointers and their binary content](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-git-large-file-storage).
Ignore generated `renders/` and `exports/` directories.
An isolated copy of the authored assets must open, render, and export without the original photo directory; reference overlays and photo comparisons additionally require `SAGE_REFERENCE_ROOT`.

Use meters, Blender Z-up, X toward the plan's right, and Y toward the rear of the house.
Place the house's front-left ground-floor plan corner at the origin, even though only two rooms are modeled.
Convert plan dimensions in feet once, and verify orientation against the shared opening and facade references.
Keep `living` and `dining` as the website's existing room IDs, on floor `0`.

Organize architecture, furniture, lighting, and reference cameras into identifiable collections.
Use one shared shell for the adjoining wall and opening, with separately hideable ceilings.
Record directly observed, plan-derived, and inferred details in `properties/sage/notes.md`, including consequential dimension conflicts.

A bootstrap script creates a new scene; rerunning it must not overwrite an existing master.
Authoring scripts state which objects they replace and preserve changes elsewhere.
Rendering, checking, and export read the saved scene without saving over it.
Optimize a separate export copy, keeping the master editable.
Use Blender's built-in renderer and glTF exporter rather than implementing substitutes.

## Export contract and website ownership

Produce `exports/sage-living-dining/scene.glb`, `scene.json`, and an export note identifying the source scene revision, Blender version, command, and known visual differences.
The GLB embeds its required textures and exports perspective walkthrough cameras as well as geometry.
Reference cameras and source-photo backgrounds stay in the authoring scene.
The website uses the GLB's camera transforms and vertical field of view directly, adjusting the aspect ratio for its canvas.
Blender performs the conversion to meters and Y-up glTF coordinates; the website applies no additional scale or axis correction.

The initial `scene.json` contract is:

```json
{
  "asset": "scene.glb",
  "floor_node": "ground_floor",
  "ceiling_nodes": ["ceiling_living", "ceiling_dining"],
  "overview_camera": "overview",
  "rooms": [
    {"id": "living", "floor": 0, "node": "living", "camera": "walk_living", "neighbors": ["dining"]},
    {"id": "dining", "floor": 0, "node": "dining", "camera": "walk_dining", "neighbors": ["living"]}
  ]
}
```

Node and camera references resolve to uniquely named objects in the loaded GLB.
Export explicit parent objects for the floor and rooms rather than relying on Blender collections becoming glTF nodes.
Room nodes contain their furniture and room-specific geometry; the shared shell and ceilings belong to the floor node.
The floor bounds provide the overview orbit target; the checker uses room nodes and floor membership to verify the exported grouping.
Room order supplies the initial room, `living`; neighboring IDs supply the two-room transition controls.
There is no separately maintained list of camera coordinates in JSON or JavaScript.

| Producer or stored artifact | Consumer and verification |
|---|---|
| Reference index and external originals | Authoring and comparison scripts resolve room, camera, arrangement, and source paths |
| Saved scene and relative textures | Blender rendering and export; an isolated asset copy proves recoverability |
| Scene objects and cameras | Exporter produces GLB and metadata together; checks reject missing or duplicate referenced objects |
| GLB and metadata | Website loader uses [GLTFLoader](https://threejs.org/docs/pages/GLTFLoader.html), room controls, camera placement, and ceiling visibility |
| Comparison images and notes | Owner evaluates resemblance and remaining uncertainty |

The website adds an unlinked, `noindex` review route at `/houses/sage/model-preview`.
It loads a copied export under its public assets and supplies room labels and interface text.
Provide room selection, mouse/touch look controls, keyboard-accessible look controls, and an overview with ceilings hidden.
Return to the selected room with its ceiling restored and its authored camera pose reset.
Expose only the two modeled rooms, with a visible loading state and an actionable asset-load error.
Reuse existing Three.js dependencies and suitable tour styling without coupling the preview to the whole-house room list, feet-based map, or procedural geometry.
The website owns browser lighting and tone mapping; comparison renders use Cycles.

Copy the complete export directory into the website explicitly and record the paired asset revision.
No shared package, server, automated publication, or generalized scene registry is needed.
Both sides of this new contract are delivered together; the existing tour is not migrated in this feature.

## Quality and acceptance

The feature is complete when all of the following hold:

1. The saved, editable scene contains both connected rooms with plan-supported proportions and orientation, recognizable major furnishings, and their photographed finishes.
2. The scene and required textures can be recovered together, and documented commands render the saved comparison cameras and export the browser assets without changing the master scene.
3. A review set contains the four or more photo/render comparisons, at least two additional viewpoints including one through the shared opening, and unresolved differences grouped by geometry, arrangement, materials, and lighting.
   Supporting views judge only details compatible with the selected arrangement; novel views test coherence rather than count as new evidence of the house.
4. The original browser prototype is captured before changes, with camera pose, viewport, and field of view recorded so the improvement can be assessed against a reproducible baseline.
   The primary photographs remain the reference for accuracy.
5. The website loads the delivered export at the correct scale and orientation, with textures intact, authored camera poses, working room transitions, and reversible ceiling cutaways.
   Desktop and narrow touch layouts work, controls remain usable, and the existing whole-house route still works.
6. The owner judges the result a recognizable improvement across the selected views, rather than only one attractive render.
   Record the owner's response and remaining limitations in the plan; technical completion alone does not satisfy this criterion.

Measure exported bytes, geometry and texture counts, load time, and interaction responsiveness on the named review device and browser.
Use those observations to choose and record a practical export budget during implementation, then check the final assets against it.
Distinguish a narrow browser viewport from verification on a physical phone.
If acceptable detail and usable interaction conflict, present the measured tradeoff for review rather than silently weakening either acceptance criterion.

Missing source coverage is handled by visible reconstruction notes, not a requirement for new capture.
Incorrect paths, missing textures, unresolved room or camera IDs, and failed asset loads need clear errors because they stop ordinary authoring or review.
This feature does not add general migration support, automatic asset repair, or cross-version Blender compatibility.
