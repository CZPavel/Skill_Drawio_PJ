"""Re-export and measure the committed paired pilot sources with the same settings."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw
from build_diagram import font
from export_drawio import export
from lint_drawio import lint

ROOT = Path(__file__).resolve().parents[1]
CASES = ("process", "topology", "dense-training")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reexport", action="store_true")
    args = parser.parse_args()
    summaries = []
    reports = ROOT / "benchmark/reports"
    reports.mkdir(parents=True, exist_ok=True)
    for case in CASES:
        for variant in ("official", "pj"):
            source = ROOT / (f"benchmark/official/{case}.drawio" if variant == "official" else f"examples/{case}/{case}.drawio")
            outdir = ROOT / "benchmark" / variant
            outdir.mkdir(parents=True, exist_ok=True)
            if args.reexport:
                result = export(source, formats=["svg", "png"], output_dir=outdir)
                # Public manifests contain only portable identities. Private command paths stay local.
                public = {"source": source.relative_to(ROOT).as_posix(), "source_sha256": result["source_sha256"],
                    "drawio_version": result["drawio_version"], "page_index": result["page_index"],
                    "settings": {"theme": "light", "border": 16, "png_scale": 2, "embed_diagram": True, "embed_svg_fonts": False},
                    "files": [{**f, "path": Path(f["path"]).relative_to(ROOT).as_posix()} for f in result["files"]]}
                Path(result["manifest"]).write_text(json.dumps(public, indent=2) + "\n", encoding="utf-8")
            native = lint(source, target_width_mm=160)
            native["source"] = source.relative_to(ROOT).as_posix()
            (reports / f"{variant}-{case}.source.json").write_text(json.dumps(native, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            svg = outdir / f"{case}.svg"
            process = subprocess.run(["node", str(ROOT / "scripts/audit_svg.cjs"), str(svg), "--target-width-mm", "160"], capture_output=True, text=True, encoding="utf-8", timeout=45)
            if process.returncode:
                raise RuntimeError(process.stderr)
            audit = json.loads(process.stdout)
            audit["source"] = svg.relative_to(ROOT).as_posix()
            (reports / f"{variant}-{case}.rendered.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            svgroot = ET.parse(svg).getroot()
            width, height = [float(v) for v in svgroot.get("viewBox").split()[2:]]
            summaries.append({"case": case, "variant": variant, "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "export_width": width, "export_height": height, "height_at_160mm": height / width * 160,
                "rendered_metrics": audit["metrics"],
                "source_findings": dict(Counter(f["code"] for f in native["findings"])),
                "rendered_findings": dict(Counter(f["code"] for f in audit["findings"]))})
        images = []
        for variant in ("official", "pj"):
            original = Image.open(ROOT / f"benchmark/{variant}/{case}.png").convert("RGB")
            images.append(original.resize((780, round(original.height * 780 / original.width)), Image.Resampling.LANCZOS))
        canvas = Image.new("RGB", (1640, max(im.height for im in images) + 100), "#F2F5F7")
        draw = ImageDraw.Draw(canvas)
        for x, label, image in zip((25, 835), ("Official JGraph workflow", "Skill_Drawio_PJ"), images):
            draw.text((x, 24), label, font=font(28, True), fill="#182B3B")
            canvas.paste(image, (x, 80))
        canvas.save(ROOT / f"benchmark/{case}-comparison.png")
    (ROOT / "benchmark/metrics.json").write_text(json.dumps(summaries, indent=2) + "\n", encoding="utf-8")
    for item in summaries:
        metrics = item["rendered_metrics"]
        print(f"{item['case']:16} {item['variant']:8} height={item['height_at_160mm']:.1f}mm minfont={metrics['projected_min_font_pt']:.2f}pt bends={metrics['bends']} findings={item['rendered_findings']}")


if __name__ == "__main__":
    main()
