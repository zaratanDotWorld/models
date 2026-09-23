# Sage reconstruction textures

`living-wallpaper.webp` and `dining-wallpaper.webp` are generated approximations copied from the existing Sage website prototype.
They were generated on September 18, 2026 from text prompts describing the visible wallpaper and are not scans of the house surfaces.
The original attribution and prompts remain in `website/public/images/sage-tour/materials/README.md`.
Blender stores both image paths relative to `sage.blend`.

The `tour-*.png` files come from the existing Sage tour's procedural canvas materials through its native glTF download and Blender's native glTF importer.
They provide the wood floor, rug, tabletop, upholstery, and furnishing finishes used by the imported living and dining furniture groups.
Their source GLB SHA-256 is stored on the Blender scene when `scripts/import_sage_furniture.py` runs.
