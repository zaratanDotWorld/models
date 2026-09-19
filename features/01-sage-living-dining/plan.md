# Sage living and dining implementation plan

Status: not started.
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

- [ ] Inspect the original-resolution room photos and plans; populate `properties/sage/references.json` with the two primary images and supporting views.
- [ ] Record the selected arrangement, dimensions, source conflicts, and inferred areas in `properties/sage/notes.md`.
  Select at least two supporting comparison photos that add useful architectural coverage.
- [ ] Capture the current website prototype's living and dining views and record browser, viewport, camera pose, and field of view before changing the consumer.
- [ ] Set up Blender 4.5.14 LTS and Git LFS; document `BLENDER_BIN`, `SAGE_REFERENCE_ROOT`, local prerequisites, and the supported invocation from the repository root.
  Use Blender's bundled Python; no application runtime or package manager is needed in models.
- [ ] Add LFS rules for the `.blend` scene and derived texture binaries, plus ignore rules for renders, exports, and machine-specific configuration.
  Leave original source photographs in Dropbox.

Evidence: selected references exist and are readable, their room/arrangement associations are documented, baseline screenshots are saved, and the pinned Blender executable starts in background mode.
Record evidence paths in this plan; do not mark reconstruction acceptance complete at this stage.

## B — Prove the scene and browser contract

- [ ] Add the scene bootstrap and a first saved `properties/sage/sage.blend` with plan-scaled floors, walls, shared opening, hideable ceilings, and walkthrough/overview cameras.
  Document object ownership and refuse to bootstrap over an existing master.
- [ ] Implement commands for rendering saved cameras, exporting the saved scene, and checking source assets and export structure.
  Use Blender's native APIs and exporter, with failures returning a nonzero process exit code.
- [ ] Produce GLB and JSON together using the feature's contract, including explicit room/floor parent nodes and unique camera names.
  Keep reference backgrounds and render-only lighting out of the browser export.
- [ ] Add the website's minimal `/houses/sage/model-preview` route and load the generated pair through `GLTFLoader`.
  Use the existing website's pnpm setup and Three.js dependency.
- [ ] Verify one known measured span and an asymmetric room/opening landmark after loading, as well as both camera world transforms and field of view.
  Confirm that the loader resolves all metadata references and does not apply the old feet scale or invert the house.

Evidence: Blender-generated geometry loads in the real consumer, cameras point into the intended rooms, and the scene reads consistently with the plan.
This is the first contract check, not a visual-quality milestone.

## C — Reconstruct and compare

- [ ] Match at least four reference cameras to the selected photos using fixed architectural landmarks and plan dimensions.
  Save poses, projection settings, and source associations in the scene and reference index.
- [ ] Refine the shell: openings, windows, paneling, ceiling heights, trim, and the shared doorway.
  Resolve orientation and dimensional disagreements before detailing furniture.
- [ ] Reconstruct the major furniture and distinctive decoration in the chosen arrangement, including the living-room seating and shelving and dining-room cabinet, table, benches, and chandelier.
- [ ] Prepare derived surface textures with source attribution and relative paths; reproduce wallpaper, wood, textiles, and visible glass as closely as the evidence permits.
  Record consequential approximations rather than treating generated detail as observed fact.
- [ ] Set Cycles lighting and render the saved reference views at matching aspect ratios.
  Save repeatable render settings and side-by-side photo/render comparisons under ignored `renders/`.
- [ ] Inspect at least two additional viewpoints, including one across the shared opening; correct intersections, floating objects, incomplete visible surfaces, and single-view distortions.
- [ ] Iterate on the largest remaining differences and record unresolved ones in the reconstruction notes.

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

Implementation checks have not run; there is no Blender scene or browser export in this repository yet.
Record actual commands, results, artifact paths, device/browser details, and the owner's visual judgment here as chunks complete.
The feature's design review is separate from acceptance of the future reconstruction.
