# Zaratan Models — Architecture

This document describes the intended architecture.
The repository currently contains documentation only; the Blender workflow and website integration described below are proposed work.

## Repository boundary

`zaratanDotWorld/models` owns reconstruction: reference mapping, Blender scenes, modeling scripts, materials, render comparisons, and asset export.
`zaratanDotWorld/website` owns presentation: the Three.js viewer, navigation controls, room descriptions, accessibility, analytics, and publication.

The connection is an exported GLB plus room and viewpoint metadata.
Start with an explicit export-and-copy step between checkouts.
A service, shared package, or automated publication pipeline is unnecessary for the first scene.

```text
Existing photographs + floor plans + owner corrections
                         |
              Reference mapping and camera matching
                         |
                Blender scene + Python scripts
                         |
              Render, compare, and revise
                         |
            Optimized GLB + room/viewpoint metadata
                         |
              Website's Three.js walkthrough
```

## Authoring and scene ownership

Blender is the authoring environment, with Python scripts using its built-in API for construction, targeted revisions, rendering, and export.
Use Blender's existing modeling and glTF export tools rather than implementing a modeling engine or file exporter.

The saved `.blend` scene owns current object geometry, transforms, materials, lighting, and cameras.
Scripts operate on explicitly named objects or collections and preserve authored work outside their scope.
A script that regenerates an object should make that ownership clear so later runs do not silently overwrite manual refinements.

Organize the scene by floor and room, with architecture, furniture, and lighting identifiable within that structure.
Shared architectural elements such as a doorway or adjoining wall have one geometric representation.
Keep room IDs stable between source mapping, scene organization, and the website export.

Use detailed geometry and materials in the authoring scene.
Optimization happens on an export copy, preserving the editable source.
Cycles renders support visual comparison; the website uses its own real-time lighting and materials.

## Source references

The original source collection remains at a locally configured directory, currently:

```text
/Users/kronosapiens/Library/CloudStorage/Dropbox/Documents/Work/Zaratan/Sage
```

Store source filenames relative to that directory in a reference index.
The index associates photographs and drawings with room IDs, represented arrangements, and relevant observations.
A simple readable file is sufficient; its format belongs to the first feature.
Derived textures retain their source filenames and any reconstruction or generation notes.

The current Sage references include:

| Relative path | Use |
|---|---|
| `photos/floorplan/fplan-sketch-lower.jpg`, `fplan-sketch-upper.jpg` | Owner-confirmed current room layout and numbering |
| `design/floor-plans.pdf` | Architectural dimensions, sheets A2.0 and A2.1 |
| `design/approved plans/215-plan-set-final.pdf` | Roof plan and exterior elevations |
| `photos/house/` | Shared rooms, circulation, finishes, and furnishings |
| `photos/rooms/` | Labeled bedroom references |
| `photos/top-360/215-N-Ave-56/` | Additional listing photographs, including exterior views |
| `photos/renovation/aerial-shot.png` | Existing overhead context for the exterior |

The owner confirmed that `photos/house/bathroom.JPG` shows the upstairs bathroom beside the library and that its vanity is navy.
Rooms 2, 3, and 4 have no matched room photos and remain deferred.
Room 7 is represented unfurnished to match its reference.
The other bathrooms still lack matched finish references.
These observations do not imply that all other surfaces or furniture dimensions are known.

Document whether a modeled detail is directly supported, dimensioned from a plan, or inferred.
This can remain room-level notes with exceptions for consequential details.
Do not treat generated images or the prototype's approximations as evidence of the real house.

## Geometry, units, and cameras

Use meters for Blender scene geometry.
Convert dimensions given in feet once when bringing them into the scene.
Use Blender's Z-up coordinates, with X running left to right on the plan and Y toward the rear of the house.
Validate orientation against facade photographs and room connections to avoid mirroring the plan.

Create named reference cameras for photographs used in comparisons.
Estimate viewpoint and field of view from architectural lines and known dimensions; retain those settings in the scene.
Walkthrough viewpoints are separate named cameras chosen for navigation and visibility.

Blender's glTF exporter converts the scene to glTF's Y-up convention.
Export viewpoint transforms in that same convention and unit system.
The website consumes those transforms directly without a second feet-to-meters conversion.

## Materials and visual review

Use physically based materials and image textures, recovering visible patterns from source photos where practical.
Separate surface appearance from illumination when preparing textures.
Lighting follows the conditions supported by the reference set; differences between photographs remain visible in review notes.

For each meaningful revision, render the selected reference cameras and compare them with the corresponding photographs.
Also inspect additional viewpoints for intersections, missing surfaces, and inconsistent object depth.
Keep the comparison inputs, relevant render settings, and unresolved differences together so the next revision has a useful baseline.

A high-quality Blender render and a usable browser scene are separate deliverables.
Check the export in the website after material simplification and optimization.
Bake supported appearance into textures where needed and record consequential differences that cannot be reproduced in the viewer.

## Export and website integration

The export contains:

- A GLB with geometry, materials, textures, and identifiable floor, room, exterior, and ceiling groups needed by the viewer.
- Metadata mapping room IDs to floor membership, scene groups, walkthrough viewpoints, and neighboring rooms.
- A brief export note identifying the source scene, Blender version, and known limitations.

The first integration feature defines the exact metadata shape against the website's existing room and camera consumers.
Viewpoint transforms come from the scene, rather than a separately maintained set of coordinates.
The website supplies applicant-facing descriptions and interface behavior.

Verify scale, orientation, textures, floor cutaways, room transitions, and visual quality in the consumer.
Choose polygon, texture, and loading budgets from the first scene's actual browser behavior.

The website's `components/sage-tour/house.js` currently owns dimensions, IDs, connectivity, and viewpoints.
Its modeling modules generate the current geometry.
Those files provide an initial reference, with the original plans and photographs used to resolve discrepancies.
Replacing that generated geometry and consuming exports is future website work, scoped in a feature that names both repositories.
This documentation change does not migrate or remove the existing prototype.

## Files and tooling

Create directories as feature work needs them:

| Proposed path | Responsibility |
|---|---|
| `properties/sage/` | Scene, reference index, derived materials, camera associations, and reconstruction notes |
| `scripts/` | Blender authoring, rendering, verification, and export commands |
| `renders/` | Generated comparisons and review images |
| `exports/` | Generated delivery assets |
| `features/<NN>-<name>/` | Feature specification and implementation plan |

Track specifications, scripts, and small reference metadata in Git.
Keep the original photo collection outside the repository.
Select storage and versioning for large `.blend` files, derived textures, renders, and exports in the first implementation feature.
The editable scene and its required textures need a recoverable version together; regenerated outputs can remain disposable.

Pin and document the Blender version when the first runnable scene is introduced.
Use its bundled Python and built-in APIs initially, adding dependencies only for demonstrated needs.
Setup, render, and export commands will be documented once implemented.

## Verification and evolution

Visual comparison is the primary check for reconstruction quality.
Automated checks cover consequential structural behavior such as units, room IDs, exported camera transforms, and required textures.
Browser checks establish whether the exported scene works in the walkthrough.
Neither a successful export nor a plausible render alone establishes fidelity.

The first living-and-dining feature establishes the working scene, reference format, storage choice, and export contract.
Expand reusable helpers when another room demonstrates a shared need.
More automated reconstruction techniques can be evaluated against the same references and visual criteria without changing the repository's role.
