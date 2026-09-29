# Sage exterior completion plan

Status: active; exterior implementation is verified and accepted by the owner, with publication pending.
Scope and acceptance are in the [specification](spec.md).

## Resume

The owner accepted the exterior comparison gallery at `renders/sage-exterior-completion/index.html` on 2026-09-29.
The current review and verification handoff is `.development-workflow-run.rear-patio/handoff.md`.
Keep the user-selected `gpt-5.6-sol` implementer and independent `gpt-6-astra` reviewers; do not silently substitute models.
Read the current [asset manifest](../../properties/sage/assets.json) and [reconstruction notes](../../properties/sage/notes.md).
On a fresh checkout, run `python3 scripts/sage_assets.py fetch` before opening the master.
Local setup and the native checks are documented in [README](../../README.md).

## Baseline

The completed front/rear pass corrected the porch, entrance steps and grade joins, projecting window trim, and rear platform, supports, and stairs.
Its master SHA-256 is `2d238e0f7a34b1982a6055cfcb1011e4b208328932bc833425d3cdb786cf990b`.
Native detailed-room, house, and site checks passed, along with actual GLB reimport and repeated-builder checks.
Independent design and code review, deletion review, and final audit are complete for that pass.
The detailed-room geometry, materials, saved world, and texture/furniture payloads were preserved.

Local comparisons are in `renders/sage-exterior-details/index.html`, with the site overview in `renders/sage-site-layout/index.html`.
Local review evidence remains in `.development-workflow-run.exterior-fidelity/`; that completed run has no active state file.
These ignored outputs supplement the committed notes and scripts and can be regenerated.

## Sequence

- [x] Inventory side-elevation, roof, detached-unit, garage, and ground references; identify supported changes and important unknowns.
- [x] Review the design and establish preservation snapshots before editing.
- [x] Refine main-house sides and roof connections, then compare against the front/rear baseline.
- [x] Refine the detached unit and garage, retaining plan-controlled placement and dimensions.
- [x] Reconcile paths, grade transitions, bases, and access across the full site.
- [x] Regenerate comparisons and exports, and verify preservation and repeatability.
- [x] Add the omitted covered rear patio and reconcile its utility enclosure and yard access against the current plan and older photographs.
- [x] Complete owner visual acceptance.
- [ ] Publish the recoverable asset bundle and checkpoint the source changes.

The gallery includes six source/model pairs and north, south, roof, courtyard circulation, and rear-patio diagnostics.
Native checks, exported geometry and materials, isolated bundle recovery, and repeated site-only and house-plus-site builds are verified locally.
Detailed interiors, the canonical house layout, and the main-house windows and roofs remain preserved.
The owner's grade correction removes the invented front slope and extends the house base to roughly level ground around the site.
Paths, rear access and support posts meet that ground, while the detached unit and garage retain their geometry at the corrected elevation.
The covered rear patio now includes its raised slab, rounded stucco openings, metal guard, concrete side steps and adjacent utility enclosure.
The current plan governs rear apertures; older photographs establish the patio form and finishes.
The published asset manifest still describes the previous Release; the current candidate is local.

After exterior acceptance, queue interior architecture around stairs, circulation, openings, and fixed finishes before furnishings.
The original two-room feature's unfinished browser work remains recorded in its [plan](../01-sage-living-dining/plan.md).
