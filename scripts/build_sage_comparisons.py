import html
import json
import os
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "renders/comparisons"
CAMERAS = ["ref_living_primary", "ref_living_opening", "ref_dining_primary", "ref_dining_cabinet"]


def main():
    reference_root = os.environ.get("SAGE_REFERENCE_ROOT")
    if not reference_root:
        raise RuntimeError("SAGE_REFERENCE_ROOT is required")
    records = json.loads((ROOT / "properties/sage/references.json").read_text())["references"]
    by_camera = {record.get("camera"): record for record in records}
    source_dir = OUTPUT / "source"
    source_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for camera in CAMERAS:
        record = by_camera[camera]
        source = Path(reference_root) / record["path"]
        render = ROOT / "renders/reconstruction" / f"{camera}.png"
        if not source.is_file():
            raise RuntimeError(f"Missing source reference: {source}")
        if not render.is_file():
            raise RuntimeError(f"Missing reconstruction render: {render}")
        copied = source_dir / f"{camera}{source.suffix}"
        shutil.copy2(source, copied)
        exclusions = record.get("comparison_exclusions") or ["None recorded."]
        notes = f'<p><strong>Reconstructed arrangement:</strong> personal, March 2023.</p><p><strong>Photo arrangement:</strong> {html.escape(record["arrangement"])}</p><p><strong>Comparison exclusions:</strong> {html.escape(" ".join(exclusions))}</p>'
        rows.append(f'<section><h2>{html.escape(camera)}</h2>{notes}<div><figure><img src="source/{copied.name}"><figcaption>Source: {html.escape(record["path"])}</figcaption></figure><figure><img src="../reconstruction/{camera}.png"><figcaption>Cycles reconstruction</figcaption></figure></div></section>')
    limitations = '<aside><h2>Current limitations</h2><p>The reference camera poses are matched by eye from EXIF starting projections, not solved calibrations.</p><p>Unmeasured furniture dimensions, kitchen depth, colors, and lighting remain approximate.</p><p>See <a href="../../properties/sage/notes.md">the reconstruction notes</a> for the recorded evidence and remaining differences.</p></aside>'
    document = """<!doctype html><html><head><meta charset="utf-8"><title>Sage comparisons</title><style>body{font:16px system-ui;background:#211d18;color:#f4eadb;margin:2rem}section{margin-bottom:3rem}section>div{display:grid;grid-template-columns:1fr 1fr;gap:1rem;align-items:start}figure{margin:0}img{display:block;width:100%;max-height:78vh;object-fit:contain;background:#111}figcaption{margin-top:.5rem;color:#cbbba4}aside{border:1px solid #6f604d;padding:1rem 1.25rem;margin:1rem 0 3rem}a{color:#f2c786}@media(max-width:800px){section>div{grid-template-columns:1fr}}</style></head><body><h1>Sage living and dining comparisons</h1>""" + limitations + "".join(rows) + "</body></html>"
    (OUTPUT / "index.html").write_text(document)
    print(f"Wrote {OUTPUT / 'index.html'}")


if __name__ == "__main__":
    main()
