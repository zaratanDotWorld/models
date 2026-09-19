# Zaratan Models — Product

This document describes the project's purpose and intended outcomes.
Feature specs and plans define bounded deliveries against that direction.

## Purpose

Reconstruct recognizable, visually convincing, editable 3D models of Zaratan's coliving houses from existing still photographs and floor plans.
Sage House, at 215 N Avenue 56, Los Angeles, CA 90042, is the first subject.

The experiment tests how far an AI agent can take interpretation, modeling, and iterative visual correction with a fixed set of references.
The agent supplies the reconstruction work; Blender supplies the authoring and rendering tools.

The eventual use is a shareable browser walkthrough that helps applicants understand the house without an in-person tour.
The reconstruction belongs in this repository, while the applicant experience belongs in the Zaratan website.

## Users and outcomes

The owner reviews whether the scene represents the actual house and identifies errors that the references alone cannot resolve.
The agent or a future modeler needs an editable scene, identifiable sources, and a repeatable way to compare revisions.
Applicants need recognizable rooms, understandable connections between spaces, and a usable tour on their phones.

Success combines three qualities:

- **Appearance:** architecture, finishes, furniture, and decoration resemble the photographs.
- **Spatial coherence:** dimensions, openings, placement, and room connections agree across views.
- **Usefulness:** the exported scene preserves enough detail and responsiveness for the website walkthrough.

Photographic realism and factual accuracy are evaluated separately.
A plausible unseen surface remains an inference, even when it looks convincing.

## Scope

Use the existing image collection, architectural drawings, owner-confirmed room plans, and corrections already supplied.
Reconstruct building geometry, distinctive furnishings, materials, lighting, and camera viewpoints.
Keep sources and material assumptions identifiable so revisions can improve fidelity without losing the basis for earlier work.

New photographs, video, LiDAR, and on-site scanning are outside this experiment.
Missing coverage is a limitation to record, not a prerequisite for continuing.
Rooms 2, 3, and 4 are deferred until the owner chooses to revisit their references.

The project does not initially include a capture service, a general-purpose modeling platform, renovation management, or a replacement for the website.
Dimensions are for visualization; the model is not a measured survey or a construction document.

## Reconstruction process

1. Associate references with rooms and identify which photographs depict the same arrangement.
   When photographs conflict, document the arrangement being represented and the evidence for it.
2. Use plans to establish scale and connectivity, then match cameras to the photographs.
3. Refine geometry, furnishings, and materials against multiple views of the same space.
4. Compare rendered images with the references and inspect additional viewpoints for geometric consistency.
5. Prepare a browser export and evaluate it in the website viewer.

Visible patterns and objects should follow the photographs where the image quality permits.
Generated textures and inferred details are documented approximations, not additional evidence about the house.

## Evaluating quality

Review uses corresponding photographs and renders, with comparable camera position, framing, and perspective.
Assess room proportions, opening placement, furniture silhouettes, material appearance, and lighting separately.
Inspect viewpoints between the references to detect geometry that only works from one camera.

The current Three.js prototype is the baseline.
A convincing improvement preserves recognizable details across several views and produces a coherent editable scene.
A single attractive render is insufficient evidence for a successful walkthrough.

The owner provides the judgment of resemblance.
Render comparisons, unresolved differences, and browser checks provide review evidence.
Feature plans define the views and checks needed for their scope; numerical image similarity alone does not establish fidelity.

## First experiment and expansion

Begin with the connected living and dining rooms, which have references for architecture, furniture, and distinctive finishes.
The first feature should establish camera matching, an editable Blender scene, render comparisons, and a browser export of those spaces.

Use that result to decide whether to extend the method to other photographed rooms and the exterior.
The broader Sage reconstruction remains the direction, but whole-house photorealism is not an assumed outcome of the first feature.
Other Zaratan houses become relevant after the method proves useful on Sage.

Later feature work can define browser performance targets, asset storage, and the level of refinement justified by the available evidence.
