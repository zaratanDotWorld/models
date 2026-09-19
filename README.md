# Zaratan Models

Editable 3D reconstructions of Zaratan's coliving houses, starting with Sage House in Los Angeles.

The experiment is to determine how realistically an AI agent can reconstruct an existing house from a fixed collection of still photographs and floor plans.
Additional photography, video, and scanning are outside the initial scope.

Blender is the planned authoring environment.
The [Zaratan website](https://github.com/zaratanDotWorld/website) remains responsible for the Three.js walkthrough used by prospective residents.

## Status

This repository currently contains the initial product and architecture specifications.
Blender scenes, modeling scripts, and an export pipeline have not been implemented here.
The existing Sage prototype lives in the website repository.

The proposed first feature is a detailed reconstruction of the connected living and dining rooms.
Its scope and implementation plan will be written before modeling begins.

## Documentation and development

- [Product specification](spec/product.md): purpose, scope, users, and how reconstruction quality is judged.
- [Architecture](spec/arch.md): scene authoring, source references, visual review, and the website export boundary.
- `features/<NN>-<name>/spec.md`: a bounded feature's outcome, scope, design, and acceptance criteria.
- `features/<NN>-<name>/plan.md`: implementation chunks, dependencies, progress, and verification evidence.

The `features/` layout follows CorollaryStudio and will be created with the first feature.
Feature directories are numbered in the order work begins.

Use the installed `/development-workflow` skill to define, plan, implement, review, and close features.
It is an agent skill, not a repository command or an installed project dependency.
The reference workflow is practiced in `/Users/kronosapiens/code/td/CorollaryStudio`.

The documents in `spec/` describe durable intent and evolve with the project.
An active feature's spec and plan describe the change being built.
A shipped feature records its delivered scope and reasoning; current code and verification establish what runs today.
Keep implementation progress in the feature plan and carry enduring changes into the owning specification.
These initial documents describe direction, not completed implementation.

Commits, pushes, and pull requests require explicit user authorization.

## Working materials

The original Sage references remain in Dropbox:

```text
/Users/kronosapiens/Library/CloudStorage/Dropbox/Documents/Work/Zaratan/Sage
```

See the [source references](spec/arch.md#source-references) for the relevant plans and photographs.
A future local configuration will map the source directory; machine-specific paths do not belong in modeling scripts.

The existing prototype is in `components/sage-tour/` of the website checkout at `/Users/kronosapiens/code/zaratan/website`.
Its measurements, room IDs, and exported geometry are starting references, subject to comparison with the original plans and photos.

## Intended workflow

Existing references → Blender scene → render comparisons → optimized GLB and room metadata → website walkthrough.

Blender's Python API will support scene construction, revisions, rendering, and export.
Setup commands, the supported Blender version, and asset storage will be established by the first implementation feature.
There is no application server, package installation, or build command in this repository yet.
