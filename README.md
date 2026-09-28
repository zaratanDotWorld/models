# Zaratan Models

Editable 3D reconstructions of Zaratan's coliving houses, starting with Sage House in Los Angeles.

The experiment is to determine how realistically an AI agent can reconstruct an existing house from a fixed collection of still photographs and floor plans.
Additional photography, video, and scanning are outside the initial scope.

Blender is the planned authoring environment.
The [Zaratan website](https://github.com/zaratanDotWorld/website) remains responsible for the Three.js walkthrough used by prospective residents.

## Status

This repository contains the initial product and architecture specifications and the source mapping for the first reconstruction.
Blender scene construction and the export pipeline are in progress.
The existing Sage prototype lives in the website repository.

The first feature is scoped as a detailed reconstruction of the connected living and dining rooms, including photo comparisons and a two-room website preview.
Its [specification](features/01-sage-living-dining/spec.md) and [implementation plan](features/01-sage-living-dining/plan.md) are active.

## Documentation and development

- [Product specification](spec/product.md): purpose, scope, users, and how reconstruction quality is judged.
- [Architecture](spec/arch.md): scene authoring, source references, visual review, and the website export boundary.
- `features/<NN>-<name>/spec.md`: a bounded feature's outcome, scope, design, and acceptance criteria.
- `features/<NN>-<name>/plan.md`: implementation chunks, dependencies, progress, and verification evidence.

The `features/` layout follows CorollaryStudio.
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

Public [architectural drawing extracts](properties/sage/plans/README.md) are available in this repository through Git LFS.
See the [source references](spec/arch.md#source-references) for the private originals and photographs.
Set `SAGE_REFERENCE_ROOT` to map this source directory; machine-specific paths do not belong in modeling scripts.

The existing prototype is in `components/sage-tour/` of the website checkout at `/Users/kronosapiens/code/zaratan/website`.
Its measurements, room IDs, and exported geometry are starting references, subject to comparison with the original plans and photos.

## Local setup

The supported authoring version is Blender 4.5.14 LTS for Apple Silicon.
This checkout can use repository-local tools without changing the system installation:

Download the official [Blender 4.5.14 Apple Silicon disk image](https://download.blender.org/release/Blender4.5/blender-4.5.14-macos-arm64.dmg) and verify its SHA-256 as `65134d9b07b20e2fa8d3c9e44f6f44ffb5c9774dd521b95f50387310241ca170` before copying `Blender.app` to `.local/blender/Blender.app`.
Download the official [Git LFS 3.8.0 release](https://github.com/git-lfs/git-lfs/releases/tag/v3.8.0), verify the Darwin ARM64 zip SHA-256 as `caff76a7d070d8160c89bc39b6e85d98f24135b6fed038a3b4de2590d25102d8`, and place its `git-lfs` executable in `.local/bin/`.
An existing Git LFS 3.8.0 installation on `PATH` can be used instead.

```sh
export PATH="$PWD/.local/bin:$PATH"
export BLENDER_BIN="$PWD/.local/blender/Blender.app/Contents/MacOS/Blender"
export SAGE_REFERENCE_ROOT="/absolute/path/to/Sage"
```

`SAGE_REFERENCE_ROOT` must contain the relative paths recorded in `properties/sage/references.json`.
Original photographs and complete drawing sets remain outside this repository.
Blender uses its bundled Python, so this repository needs no application runtime or package manager.

Confirm the local prerequisites from the repository root:

```sh
"$BLENDER_BIN" --background --factory-startup --python-exit-code 1 --python-expr 'import bpy,sys; print(bpy.app.version_string); print(sys.version); assert bpy.app.version == (4, 5, 14)'
git lfs version
```

On macOS, Blender background commands may need permission to access the Metal device during startup.
Git LFS is configured for this repository with `git lfs install --local`.
The master `.blend` file, derived texture binaries under `properties/sage/textures/`, and architectural PDF extracts under `properties/sage/plans/` use LFS.
Generated `renders/` and `exports/` remain ignored.

Create the Sage master once from the repository root:

```sh
"$BLENDER_BIN" --background --factory-startup --python-exit-code 1 --python scripts/bootstrap_sage.py
```

The bootstrap owns only initial scene creation and refuses to overwrite `properties/sage/sage.blend`.
The saved scene is authoritative after creation.
Run the mutating authoring steps in this order, then check the saved scene:

```sh
"$BLENDER_BIN" --background properties/sage/sage.blend --python-exit-code 1 --python scripts/update_sage_detail.py
"$BLENDER_BIN" --background properties/sage/sage.blend --python-exit-code 1 --python scripts/import_sage_furniture.py
"$BLENDER_BIN" --background properties/sage/sage.blend --python-exit-code 1 --python scripts/check_sage.py
```

The updater owns `C_DETAIL`, `C_AUTHORING`, the named shared-wall and threshold geometry, the first canonical dining floor and ceiling migration, obsolete shell visibility, ceiling and shared-opening materials, and reference-camera settings.
The furniture importer replaces `C_IMPORTED_FURNITURE`, removes the superseded rough furniture, places the dining table and living side-window curtains, stores their required textures beside the master, and saves the loaded master.
Set `SAGE_FURNITURE_GLB` when the unbatched native export is not at `.local/sage-furniture-unbatched.glb`.

Run the read-only check, render, and export commands with:

```sh
"$BLENDER_BIN" --background properties/sage/sage.blend --python-exit-code 1 --python scripts/check_sage.py
"$BLENDER_BIN" --background properties/sage/sage.blend --python-exit-code 1 --python scripts/render_sage.py
"$BLENDER_BIN" --background properties/sage/sage.blend --python-exit-code 1 --python scripts/export_sage.py
```

The check, render, and export commands do not save over the loaded scene.
The renderer writes disposable images to `renders/reconstruction/`, and the exporter writes `scene.glb`, `scene.json`, and an export note to `exports/sage-living-dining/`.
Set `SAGE_RENDER_SCALE=2` for the 960 by 1280 primary comparisons and 1280-pixel-wide supporting and novel views.
Set `SAGE_RENDER_SAMPLES` to change the default 32 Cycles samples, or set `SAGE_RENDER_ENGINE=BLENDER_EEVEE_NEXT` for iteration previews.

Build the side-by-side comparison page after rendering:

```sh
SAGE_REFERENCE_ROOT="/absolute/path/to/Sage" python3 scripts/build_sage_comparisons.py
```

The comparison command copies the four selected source images without modifying them and writes `renders/comparisons/index.html`.
Copy the complete export directory to the website's `public/models/sage-living-dining/` directory to update the unlinked review route at `/houses/sage/model-preview`.

Apply the canonical two-floor layout after the detailed rooms are present:

```sh
"$BLENDER_BIN" --background properties/sage/sage.blend --python-exit-code 1 --python scripts/update_sage_house.py
```

This mutating command replaces only `HOUSE_LAYOUT` and `HOUSE_LAYOUT_CAMERAS`, hides the superseded shallow kitchen context, and preserves the detailed living and dining geometry.
It uses the right-hand A2.0 and A2.1 drawings as the architectural source.
Create the ignored source crops used by the comparison gallery with Poppler before rendering:

```sh
pdftoppm -f 1 -singlefile -r 500 -png -x 3080 -y 300 -W 2050 -H 2850 "$SAGE_REFERENCE_ROOT/design/floor-plans.pdf" .local/canonical-ground-complete
pdftoppm -f 2 -singlefile -r 500 -png -x 3100 -y 400 -W 2050 -H 2850 "$SAGE_REFERENCE_ROOT/design/floor-plans.pdf" .local/canonical-upper-complete
```

Run its read-only checks, evidence renders, and separate native export with:

```sh
"$BLENDER_BIN" --background properties/sage/sage.blend --python-exit-code 1 --python scripts/check_sage_house.py
"$BLENDER_BIN" --background properties/sage/sage.blend --python-exit-code 1 --python scripts/render_sage_house.py
"$BLENDER_BIN" --background properties/sage/sage.blend --python-exit-code 1 --python scripts/export_sage_house.py
"$BLENDER_BIN" --background --factory-startup --python-exit-code 1 --python scripts/check_sage_house_glb.py -- exports/sage-house-layout/scene.glb
```

The renderer writes labeled ground and upper plans, front and rear cutaways, and a source/model gallery to `renders/sage-house-layout/`.
The full-house exporter writes `exports/sage-house-layout/scene.glb` and its source note without changing the existing two-room browser contract.

## Intended workflow

Existing references → Blender scene → render comparisons → optimized GLB and room metadata → website walkthrough.

Blender's Python API will support scene construction, revisions, rendering, and export.
The saved Blender scene remains the editable master, while the website consumes the native glTF export and metadata pair.
