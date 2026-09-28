# Sage exterior completion plan

Status: queued for the next session after `/compact`.
Scope and acceptance are in the [specification](spec.md).

## Resume

Use `/development-workflow` to inspect the references and review the bounded design before implementation.
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

- [ ] Inventory side-elevation, roof, detached-unit, garage, and ground references; identify supported changes and important unknowns.
- [ ] Review the design and establish preservation snapshots before editing.
- [ ] Refine main-house sides and roof connections, then compare against the front/rear baseline.
- [ ] Refine the detached unit and garage, retaining plan-controlled placement and dimensions.
- [ ] Reconcile paths, grade transitions, bases, and access across the full site.
- [ ] Regenerate comparisons and exports, verify preservation and repeatability, and complete independent review and owner review.

After exterior acceptance, queue interior architecture around stairs, circulation, openings, and fixed finishes before furnishings.
The original two-room feature's unfinished browser work remains recorded in its [plan](../01-sage-living-dining/plan.md).
