# Sage living and dining implementation plan

Status: active.
This plan delivers the [feature specification](spec.md) across the models and website repositories.
All paths below are proposed implementation paths unless identified as existing.

## Ownership and sequencing

- `zaratanDotWorld/models` owns reference mapping, Blender assets, scripts, comparison evidence, and the export contract.
- `zaratanDotWorld/website` owns the preview route, controls, loading behavior, and copied browser assets.
- The existing local website prototype contains uncommitted work.
  Inspect and record its status before implementation, preserve it, and keep new feature changes identifiable without committing unrelated files.

| Chunk | Depends on | Deliverable |
|---|---|---|
| A | — | References, comparison baseline, tooling, and asset storage |
| B | A | Minimal saved scene and verified Blender-to-browser contract |
| C | B | Detailed two-room reconstruction and photo comparisons |
| D | C | Optimized export and complete review interface |
| E | D | Combined verification and owner review |

The contract is exercised with simple geometry before investing in detailed modeling.
Later chunks refine that same saved scene and consumer rather than starting another pipeline.

## A — Establish references and tooling

- [x] Inspect the original-resolution room photos and plans; populate `properties/sage/references.json` with the two primary images and supporting views.
- [x] Record the selected arrangement, dimensions, source conflicts, and inferred areas in `properties/sage/notes.md`.
  Select at least two supporting comparison photos that add useful architectural coverage.
- [x] Capture the current website prototype's living and dining views and record browser, viewport, camera pose, and field of view before changing the consumer.
- [x] Set up Blender 4.5.14 LTS and Git LFS; document `BLENDER_BIN`, `SAGE_REFERENCE_ROOT`, local prerequisites, and the supported invocation from the repository root.
  Use Blender's bundled Python; no application runtime or package manager is needed in models.
- [x] Add LFS rules for the `.blend` scene and derived texture binaries, plus ignore rules for renders, exports, and machine-specific configuration.
  Leave original source photographs in Dropbox.

Evidence: selected references exist and are readable, their room/arrangement associations are documented, baseline screenshots are saved, and the pinned Blender executable starts in background mode.
Record evidence paths in this plan; do not mark reconstruction acceptance complete at this stage.

## B — Prove the scene and browser contract

- [x] Add the scene bootstrap and a first saved `properties/sage/sage.blend` with plan-scaled floors, walls, shared opening, hideable ceilings, and walkthrough/overview cameras.
  Document object ownership and refuse to bootstrap over an existing master.
- [x] Implement commands for rendering saved cameras, exporting the saved scene, and checking source assets and export structure.
  Use Blender's native APIs and exporter, with failures returning a nonzero process exit code.
- [x] Produce GLB and JSON together using the feature's contract, including explicit room/floor parent nodes and unique camera names.
  Keep reference backgrounds and render-only lighting out of the browser export.
- [x] Add the website's minimal `/houses/sage/model-preview` route and load the generated pair through `GLTFLoader`.
  Use the existing website's pnpm setup and Three.js dependency.
- [x] Verify one known measured span and an asymmetric room/opening landmark after loading, as well as both camera world transforms and field of view.
  Confirm that the loader resolves all metadata references and does not apply the old feet scale or invert the house.

Evidence: Blender-generated geometry loads in the real consumer, cameras point into the intended rooms, and the scene reads consistently with the plan.
This is the first contract check, not a visual-quality milestone.

## C — Reconstruct and compare

- [x] Match at least four reference cameras to the selected photos using fixed architectural landmarks and plan dimensions.
  Save poses, projection settings, and source associations in the scene and reference index.
- [x] Refine the shell: openings, windows, paneling, ceiling heights, trim, and the shared doorway.
  Resolve orientation and dimensional disagreements before detailing furniture.
- [x] Reconstruct the major furniture and distinctive decoration in the chosen arrangement, including the living-room seating and shelving and dining-room cabinet, table, benches, and chandelier.
- [x] Prepare derived surface textures with source attribution and relative paths; reproduce wallpaper, wood, textiles, and visible glass as closely as the evidence permits.
  Record consequential approximations rather than treating generated detail as observed fact.
- [x] Set Cycles lighting and render the saved reference views at matching aspect ratios.
  Save repeatable render settings and side-by-side photo/render comparisons under ignored `renders/`.
- [x] Inspect at least two additional viewpoints, including one across the shared opening; correct intersections, floating objects, incomplete visible surfaces, and single-view distortions.
- [x] Iterate on the largest remaining differences and record unresolved ones in the reconstruction notes.

Evidence: a comparison set for both rooms, recorded differences by category, and a coherent editable scene from viewpoints between the photographs.
Furniture differences in supporting source photos remain explicit comparison exclusions.

## D — Finish the browser preview

- [ ] Optimize a copy of the detailed scene, preserving the master and its textures.
  Bake or simplify materials as needed for glTF and record consequential differences from Cycles.
- [ ] Copy the complete export into the website's public assets and record its source revision in the export note.
- [ ] Complete two-room navigation, mouse/touch and keyboard look controls, overview orbit, ceiling toggling, and return to the authored room pose.
  Provide loading/error feedback and keep the route unlinked and `noindex`.
- [ ] Tune browser lighting and tone mapping against the primary reference views; inspect both walkthrough and overview states for missing textures or surfaces.
- [ ] Measure asset size, geometry/texture counts, initial loading, and interaction responsiveness on a named device/browser.
  Establish an evidence-based export budget, optimize where necessary, and record whether the final version meets it.

Evidence: the detailed scene works in the actual website consumer, exports retain the important photographed details, and room/overview transitions are usable in desktop and narrow touch layouts.
Report physical-phone testing separately if performed.

## E — Verify the complete delivery

- [ ] Reopen an isolated copy of the master and its required textures with the original photo root unavailable; render and export successfully.
  Separately verify that comparison generation resolves the configured originals.
- [ ] Run the documented render/check/export commands against the saved scene and confirm that they preserve the master file and authored changes outside any targeted update.
- [ ] Run structural checks on the actual export: meter scale, orientation, room/floor grouping, camera references, neighbors, and required textures.
  Include a meaningful failure check for a missing required asset or camera; do not build a general schema framework.
- [ ] Run the website's `pnpm build` and browser checks for the new preview and the existing `/houses/sage/tour` route.
  Check room switching, pointer/touch and keyboard controls, overview/ceiling restoration, resize, and asset-load failure feedback.
- [ ] Collect final comparisons, novel views, baseline captures, export measurements, and browser screenshots in one review set with a concise evidence index.
  Document commands that regenerate disposable outputs; retain source revision, settings, and conclusions in Git.
- [ ] Present the review set to the owner, record the resemblance judgment and remaining limitations, and address accepted in-scope corrections.
  Keep the feature active if technical checks pass but visual acceptance remains outstanding.
- [ ] Update README setup/usage and the durable specs to describe the workflow actually delivered, then complete the development-workflow review and closure.
  Commit, push, and publication remain subject to the user's explicit instructions.

## Verification record

### Chunk A — references, baseline, and tooling

Completed September 19, 2026.

- `properties/sage/references.json` records nine readable source files, their relative paths and SHA-256 digests, the selected arrangement, and four planned comparison cameras.
- `properties/sage/notes.md` records plan-supported dimensions, arrangement differences, inferred areas, and baseline reproduction details, while `properties/sage/baseline.json` pins the relevant website inputs.
- `renders/baseline/prototype-living-scene-1032x712.png` and `renders/baseline/prototype-dining-scene-1032x712.png` capture each complete scene from the pre-change website prototype at revision `78f419bfd31ed0b1a68a2b1a87dbefe34aa28e68` in headless Google Chrome 153.0.8010.48 on macOS.
- The captures used a 1440 by 900 CSS-pixel viewport, device scale factor 2, a 1032 by 712 CSS-pixel scene, and the prototype's 75-degree walk camera field of view.
- The repository-local Blender executable passed a background factory-startup check as Blender 4.5.14 LTS, build hash `62c1db4208e8`, with bundled Python 3.11.15.
- A disposable Cycles CPU render completed at 160 by 120 pixels and 8 samples in 0.23 seconds at `.local/tooling-check.png`.
- The Blender 4.5.14 Apple Silicon DMG SHA-256 was `65134d9b07b20e2fa8d3c9e44f6f44ffb5c9774dd521b95f50387310241ca170`.
- Repository-local Git LFS 3.8.0 passed `git lfs version`, and `git lfs install --local` configured the checkout.
- The Git LFS archive SHA-256 was `caff76a7d070d8160c89bc39b6e85d98f24135b6fed038a3b4de2590d25102d8`.
- `git check-attr` confirms LFS filter, diff, merge, and binary text handling for the master scene and derived texture extensions.
- Blender startup needed an unsandboxed retry on macOS because sandboxed Metal device detection terminated with a segmentation fault.

Chunk A establishes inputs and a reproducible prototype baseline only.
No Blender reconstruction or visual acceptance is claimed yet.

Chunk A passed two independent implementation reviews and a final audit with no material findings.

### Chunk B — scene and browser contract

Completed September 19, 2026.

- `scripts/bootstrap_sage.py` created `properties/sage/sage.blend` and a second invocation exited nonzero rather than overwriting the master.
- The bootstrap owns initial creation only, while `check_sage.py`, `render_sage.py`, and `export_sage.py` read the saved scene without saving it.
- The master SHA-256 remained unchanged across check, render, and export commands.
- Blender world-face checks measured the living interior at 4.9530 by 4.2164 meters and the dining interior depth at 3.6068 meters, matching A2.0's 16 feet 3 inches by 13 feet 10 inches and 11 feet 10 inches.
- The 0.5334-meter dining outward step, 2.7432-meter shared opening, 2.7432-meter ceiling height, side-wall thicknesses, and dining width remain labeled inferences for chunk C camera matching.
- A shared threshold supplies continuous floor through the opening, and `overview` hides both separate ceiling nodes.
- Native Blender export produced a 23,460-byte GLB and the specified 486-byte metadata file, with SHA-256 values `44745a0a8dcfcf2cff1b252cc48470a432ed6165eeaeb51e64d553a34968cfd7` and `1c1eb75aa90b032847478d2ae3c310357c1360e5023316f7ffd7dc716adba401`.
- The export note records source scene SHA-256 `6fcd5997310abead7627d73faef36c582505dcd6c6eb558008957944a690b88b`, repository revision, Blender version, and command.
- The actual website route `/houses/sage/model-preview` loaded the copied pair through Three.js `GLTFLoader` without a scale or axis correction.
- Browser inspection resolved every floor, room, ceiling, neighbor, and camera reference exactly once and confirmed that both room nodes and both ceilings have `ground_floor` as parent.
- Loaded geometry measured the living floor at 4.9530 by 4.2164 meters, dining depth at 3.6068 meters, right-wall offset at 0.5334 meters, and shared threshold width at 2.7432 meters.
- The imported `walk_living` and `walk_dining` cameras retained distinct world transforms and vertical fields of view of 74.999999 degrees, independent of the 16:9 render setting.
- `renders/browser/model-preview-living.png`, `model-preview-dining.png`, and `model-preview-overview.png` show both authored room cameras and a complete ceiling-free overview in headless Google Chrome 153.0.8010.48 at a 1440 by 900 CSS-pixel viewport.
- Living, dining, overview, return, and orbit controls were exercised with no browser console errors.
- Removing `walk_dining` in memory caused `check_sage.py` to exit nonzero with `Expected exactly one object named walk_dining, found 0` without changing the master.
- The website `pnpm build` passed with 13 routes, including the new static preview and the unchanged existing Sage tour.

Chunk B proves the native Blender-to-browser contract with placeholder geometry and materials.
Detailed reconstruction and visual acceptance remain in chunks C through E.

Chunk B passed two independent implementation reviews, a deletion review, and a final audit with no material findings.

### Chunk C — detailed reconstruction and comparisons

Chunk C passed two independent implementation reviews, a deletion review, and a fresh final audit with no material findings.

- `scripts/update_sage_detail.py` replaces only its named detail and authoring collections and documented shell visibility, material, and reference-camera settings in the saved master.
- The four saved comparison cameras record source associations and matched vertical fields of view of 108, 70, 107, and 70 degrees in `properties/sage/references.json`.
- The visible shell preserves the measured 4.9530 by 4.2164-meter living interior and 3.6068-meter dining depth while adding segmented window walls, foyer and kitchen openings, paneling, trim, and the shared doorway.
- The detailed scene includes the primary living seating, shelving, rug, coffee table, screen, pouf, sling chair, piano, and the dining cabinet, table, benches, chandelier, and curtains.
- `scripts/import_sage_furniture.py` uses Blender's native glTF importer to retain the existing tour's more detailed editable living and dining furniture groups, parents them to the authoritative room nodes, excludes its approximate wall skins, and removes the superseded rough furniture.
- The imported unbatched native source was 10,635,888 bytes with SHA-256 `27fd01cc2114139dc654ce90898ed859f11af0f5a1803941752e489b21b15ea1`, and the actual source digest is stored on the scene at import time.
- The native import retains unbatched editable furniture objects rather than the tour's material-batched room meshes, while excluding its wallpaper and thin oak wall skins from the authoritative shell.
- The authoritative shell provides room-specific finishes on both shared-wall faces, a shallow inferred kitchen context through the observed doorway beside the cabinet, and a finished dining west wall.
- The shared opening and kitchen doorway use continuous oak head casing joined to their jambs, and the living side-window wall carries willow wallpaper to the baseboard.
- Each dining sash retains the documented 3-foot-4-inch width inside a continuous visible oak surround, with a single non-intersecting center mullion and rail segments outside the glass openings.
- Required wallpaper approximations live beside the master with relative paths and attribution in `properties/sage/textures/README.md`.
- Cycles rendered four matched comparisons at 32 samples and matching portrait or landscape aspects, plus `novel_shared_opening` and `novel_living_corner`.
- The high-resolution evidence uses 960 by 1280 pixels for primary views and 1280 by 854 or 800 pixels for supporting and novel views on a MacBookPro18,2 with Apple M1 Max and 32 GiB memory.
- `scripts/build_sage_comparisons.py` verifies the configured original paths, copies the four unmodified sources into ignored output, and writes `renders/comparisons/index.html`.
- `properties/sage/notes.md` records the remaining geometry, arrangement, material, and lighting differences without claiming visual acceptance.
- Final scene checks and export left the master SHA-256 unchanged at `85ed80a8b359d0d987e0ff69c713615d9231275598b0b7e7f60de4e99421543c`.
- Native export produced a 4,272,084-byte GLB with SHA-256 `c82c49b78b43788762db555d7f0772ef328eacc9bd946ed5303160621f271b84` and retained only the named browser cameras.
- Temporarily removing `living-wallpaper.webp` caused the structural check to exit nonzero with the required missing-texture error, and the shell trap restored the file.
- An ignored scene-copy check confirmed that rerunning the architecture update preserves changed floor UVs, existing world strength, the imported furniture collection, and a manual property without recreating `C_living_sofa*` or `C_dining_table*` objects.
- A second ignored scene-copy check confirmed that rerunning the furniture import preserves the saved floor material, a shader-node sentinel, and changed floor UVs.
- The structural check verifies every `C_DETAIL` mesh inherits from `ground_floor` and rejects imported wallpaper or thin oak wall skins.
- The comparison page identifies the reconstructed and photo arrangements separately, records each pair's exclusions, and links to the visible limitations in `properties/sage/notes.md`.

The current right-hand A2.0 plan correction was implemented on September 19, 2026 and is pending its bounded review.

- Printed plan dimensions remain 4.9530 by 4.2164 meters for the living interior and 3.6068 meters for dining depth.
- Pixel anchors calibrated from those printed spans set the traced shared opening to 2.783 meters, its living-left offset to 0.991 meters, the shared wall to 0.279 meters, and the dining right step to 0.454 meters.
- The dining interior left faces share a 0.180-meter inset, while the foyer-side exterior face is separately traced outside the living face.
- Traced openings now include the 1.95-meter living-to-foyer opening, 0.89-meter dining-to-foyer opening, and 0.80-meter kitchen doorway.
- The dining front-right and rear-right corner forms have separate traced footprints, and the living and dining side windows use their plan-calibrated positions and documented widths.
- `renders/layout/index.html` pairs the canonical plan crop with a wall-only orthographic cutaway rendered from the saved scene.
- The structural check measures the printed spans, traced openings, shared wall, shared opening, dining outline, asymmetric corner forms, dining floor outline, floor material, hierarchy, and browser cameras from actual scene geometry.
- Six synchronized Cycles renders at 32 samples preserve the corrected shell and the selected personal-photo furniture arrangement.
- Native export reload verified the room hierarchy, three browser cameras, 75-degree walkthrough fields of view, 2.783-meter shared opening, and corrected dining floor bounds.
- Round-one correction excludes the obsolete `wall_dining_left`, and a one-meter westward ray through the dining-to-foyer opening is clear in the saved scene.
- The two editable living side-window curtain groups and their child hardware now sit 0.02 meters beyond the canonical jambs.
- Curtain placement is owned by `import_sage_furniture.py`, which reads the authored living side-window glass after `update_sage_detail.py` runs.
- An ignored isolated sequence passed bootstrap, detail update, furniture import, structural check, and native export with the bootstrap floor material intact.
- Repeating furniture import in that isolated scene preserved a changed floor UV, floor material, world strength, and an outside manual property, then passed structural check and export again.
- The full six-view Cycles set was regenerated after these corrections.
- The saved master remained unchanged across structural check and export at SHA-256 `9b1f3a01e48e41170c5c3e7c4c5860d4fbeacc61eacb576ef7ee5882fe5abc5d`.
- Native GLB reimport confirms `wall_dining_left` is absent while the required hierarchy, cameras, and measured geometry remain.
- The native GLB is 4,295,776 bytes with SHA-256 `73a1b80976a66cc618fbf1ca5880edbd514d02cd0d7549a68013dd801e7ef842`.

### Canonical whole-house layout

Implemented September 20, 2026, with the source-supported linen partition correction applied September 21, 2026.
The owner accepted the whole-house layout visually on September 22, 2026.
Feature 01 browser chunks D and E remain pending.

- The same authoritative master now includes both floors from the right-hand A2.0 and A2.1 drawings while preserving the detailed living and dining rooms.
- `HOUSE_LAYOUT` owns neutral plan-derived architecture outside the two-room `EXPORT` collection, and `HOUSE_LAYOUT_CAMERAS` owns three saved authoring views.
- The modeled upper finished floor is 3.048 meters above ground, with 9-foot ground and 8-foot-6-inch upper clear heights supported by A3.0.
- Independent checks found zero failures across 23 circulation points, 11 floor samples, three joins to the detailed rooms, five stair heights, and knee-height doorway clearance.
- Eleven printed room spans pass against actual wall ray hits, with the largest deviation below 0.9 inch.
- The full-house GLB cleanly reimports 942 objects, all stable room nodes under the correct floor, finished-floor datums at 0 and 3.048 meters, the measured BED3 width, the complete inter-floor band, and nine packed images.
- The separate full-house GLB is 4,765,892 bytes with SHA-256 `9621246a3ee075657717c790abbcf21c60e7bb5148970565967df4c492eb8980`.
- The current master SHA-256 is `f07ac789bc8c9358b5ccebd60d721faace87f577a484a1628aa77b4a2b116fed`, and read-only check, render, and export commands preserve it.
- The existing two-room GLB still reimports as 597 objects with no upper-floor or whole-house room nodes.
- An isolated detail-update and furniture-import rerun preserved all 318 normalized `HOUSE_LAYOUT` objects exactly.
- A separate updater rerun preserved an unrelated manual object property and world property in a disposable saved copy.
- An independent pre-expansion comparison found all 597 existing objects, 79 material graphs, and world settings unchanged in the final master.
- Round-one source correction moves the BATH1 doorway to its east partition at the A2.0 aperture and restores the south partition as a continuous wall.
- Round-two correction closes the A3.0 inter-floor band across the full facade while preserving the stair opening and independently hideable room ceilings.
- The September 21 correction adds the solid A2.1 linen west partition while retaining the open vestibule passage below it.
- `renders/sage-house-layout/index.html` pairs the complete source crops with labeled ground and upper plans and includes front and rear cutaways that show the stair, rear setback, and deck.
- The recessed entrance facade and twin door openings are modeled without unobserved exterior steps.
- Rear utility-basement access is limited to three visible inferred context steps outside BED2, and no third floor is modeled.
- The deck outer depth, exterior step heights, and stair riser count remain inferred where the plans do not print them.
