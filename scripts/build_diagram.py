"""Original bounded native draw.io authoring helper. No upstream engine code.

JSON controls semantic content and composition; Pillow measures actual font advances.
It intentionally does not import/edit arbitrary draw.io documents or infer topology.
"""
from __future__ import annotations
import argparse
from functools import lru_cache
import html
import json
import math
import os
from pathlib import Path
import xml.etree.ElementTree as ET
from PIL import ImageFont

ROOT = Path(__file__).resolve().parents[1]
TOKENS = json.loads((ROOT / "assets/design-tokens.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=64)
def font(size, bold=False, path=None):
    candidates = [path] if path else []
    candidates += [str(Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / ("arialbd.ttf" if bold else "arial.ttf")),
                   "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"]
    for candidate in candidates:
        if candidate:
            try:
                return ImageFont.truetype(candidate, round(size))
            except OSError:
                pass
    raise RuntimeError("No measurable font found. Supply font_path / bold_font_path in model.")


def wrap(text, width, face):
    """Wrap at spaces, preserving paragraph breaks; never clip unbreakable identifiers."""
    lines = []
    for paragraph in text.split("\n"):
        current = ""
        for word in paragraph.split():
            if face.getlength(word) > width:
                raise ValueError(f"Unbreakable text exceeds box width: {word!r}; widen the card")
            trial = (current + " " + word).strip()
            if current and face.getlength(trial) > width:
                lines.append(current)
                current = word
            else:
                current = trial
        lines.append(current)
    return lines


def measure(title, body, width, profile, font_path=None, bold_font_path=None, padding=None):
    pad = TOKENS["padding"] if padding is None else padding
    inner = width - 2 * pad
    if inner <= 0:
        raise ValueError("Card width must exceed twice its padding")
    titles = wrap(title, inner, font(profile["title"], True, bold_font_path))
    bodies = wrap(body, inner, font(profile["body"], False, font_path)) if body else []
    height = 2 * pad + len(titles) * profile["title"] * 1.2
    if bodies:
        height += 10 + len(bodies) * profile["body"] * 1.25
    return titles, bodies, math.ceil(height / 4) * 4


def style(**values):
    return ";".join(f"{key}={value}" for key, value in values.items()) + ";"


def load_preset(model):
    name = model.get("style_preset", "default")
    if not isinstance(name, str) or Path(name).name != name:
        raise ValueError("Invalid style_preset name")
    path = ROOT / "assets/styles" / (name + ".json")
    if not path.exists():
        raise ValueError(f"Unknown style preset {name}")
    return json.loads(path.read_text(encoding="utf-8-sig"))


def effective_profile(model):
    preset = load_preset(model)
    return {**TOKENS["profiles"][model.get("target", model.get("profile", "document"))],
            **preset.get("profile_overrides", {}), **model.get("profile_overrides", {})}


def build(model, output, report_path=None):
    preset = load_preset(model)
    model = dict(model)
    model["profile_overrides"] = {**preset.get("profile_overrides", {}), **model.get("profile_overrides", {})}
    model.setdefault("font_family", preset.get("font_family", TOKENS["font_family"]))
    semantic = model.get("semantic") or model.get("layout") == "semantic" or any(
        "x" not in n or "y" not in n for n in model.get("groups", []) + model.get("nodes", []))
    report = None
    if semantic:
        from layout_diagram import layout
        model, report = layout(model)
    if "target" in model:
        model["profile"] = model["target"]

    profile = {**TOKENS["profiles"][model.get("profile", "document")], **model.get("profile_overrides", {})}
    family = model.get("font_family", TOKENS["font_family"])
    ids = {"0", "1"}
    file = ET.Element("mxfile", host="Skill_Drawio_PJ")
    page = ET.SubElement(file, "diagram", id=model.get("id", "diagram"), name=model.get("name", "Diagram"))
    graph = ET.SubElement(page, "mxGraphModel", grid="1", gridSize="4", page="1", pageScale="1",
                          pageWidth=str(profile["canvas_width"]), pageHeight=str(profile["canvas_height"]),
                          background=TOKENS["background"], adaptiveColors="none")
    root = ET.SubElement(graph, "root")
    ET.SubElement(root, "mxCell", id="0")
    ET.SubElement(root, "mxCell", id="1", parent="0")
    boxes = {}

    def cell(identifier, **attrs):
        if identifier in ids:
            raise ValueError(f"Duplicate id {identifier}")
        ids.add(identifier)
        return ET.SubElement(root, "mxCell", id=identifier, **{k: str(v) for k, v in attrs.items()})

    for group in model.get("groups", []):
        parent = group.get("parent", "1")
        if parent not in ids:
            raise ValueError("Declare parent groups before children")
        colors = TOKENS["roles"][group.get("role", "note")]
        c = cell(group["id"], value=group["title"], vertex="1", parent=parent,
                 style="swimlane;" + style(startSize=60, horizontal=1, container=1, collapsible=0,
                    html=1, whiteSpace="wrap", fontFamily=family, fontSize=profile["title"], fontStyle=1,
                    fontColor=TOKENS["text"], fillColor=colors["fill"], swimlaneFillColor="#FFFFFF",
                    strokeColor=colors["stroke"], strokeWidth=TOKENS["stroke_width"], align="left", spacingLeft=20))
        ET.SubElement(c, "mxGeometry", **{k: str(group[k]) for k in ("x", "y", "width", "height")}, **{"as": "geometry"})
        boxes[group["id"]] = group

    for node in model.get("nodes", []):
        parent = node.get("parent", "1")
        if parent not in ids:
            raise ValueError(f"Unknown parent {parent}")
        body = node.get("body", "")
        decision = node.get("shape") == "decision"
        width = node.get("width")
        if width is None:
            longest = max((font(profile["title"], True, model.get("bold_font_path")).getlength(w)
                           for w in node["title"].split()), default=0)
            width = max(180, min(380, longest + 2 * TOKENS["padding"] + 4))
            if body:
                width = max(width, 300)
        pad = node.get("padding", TOKENS["padding"])
        # Diamond text occupies only the middle half of its bounding rectangle.
        text_width = width / 2 if decision else width
        titles, bodies, content_height = measure(node["title"], body, text_width, profile,
                model.get("font_path"), model.get("bold_font_path"), pad)
        height = max(node.get("height", 0), content_height * (2 if decision else 1))
        if decision:
            label = "<br>".join(html.escape(line) for line in titles + ([""] + bodies if bodies else []))
        else:
            label = f'<div style="font-size:{profile["title"]}px;font-weight:bold;line-height:1.2">' + "<br>".join(html.escape(line) for line in titles) + "</div>"
            if bodies:
                label += f'<div style="margin-top:10px;font-size:{profile["body"]}px;line-height:1.25">' + "<br>".join(html.escape(line) for line in bodies) + "</div>"
        colors = TOKENS["roles"][node.get("role", "data")]
        base = dict(rounded=1, arcSize=TOKENS["radius"], whiteSpace="wrap", html=1, align="left",
                    verticalAlign="top", spacing=0, spacingLeft=pad, spacingRight=pad, spacingTop=pad,
                    spacingBottom=pad, fontFamily=family, fontSize=profile["title"], fontColor=TOKENS["text"],
                    fillColor=colors["fill"], strokeColor=colors["stroke"], strokeWidth=TOKENS["stroke_width"])
        prefix = ""
        if decision:
            prefix = "rhombus;"
            base.update(align="center", verticalAlign="middle", fontStyle=1)
        elif node.get("shape") == "terminal":
            base.update(arcSize=50)
        elif node.get("shape"):
            base["shape"] = node["shape"]
        base.update(preset.get("vertex_style", {}))
        base.update(node.get("style", {}))
        c = cell(node["id"], value=label, vertex="1", parent=parent, style=prefix + style(**base))
        ET.SubElement(c, "mxGeometry", x=str(node["x"]), y=str(node["y"]), width=str(width), height=str(height), **{"as": "geometry"})
        if model.get("_semantic_generated") and "abstraction_level" in node:
            c.set("pjAbstractionLevel",str(node["abstraction_level"]))
        boxes[node["id"]] = {**node, "width": width, "height": height}

    def ancestors(identifier):
        chain = [identifier]
        while chain[-1] in boxes:
            chain.append(boxes[chain[-1]].get("parent", "1"))
        return chain

    for edge in model.get("edges", []):
        source, target = edge["source"], edge["target"]
        if source not in boxes or target not in boxes:
            raise ValueError(f"Unknown edge terminal {source} -> {target}")
        parent = next(a for a in ancestors(source)[1:] if a in ancestors(target)[1:])
        role = TOKENS["roles"][edge.get("role", "data")]
        options = dict(edgeStyle="orthogonalEdgeStyle", rounded=0, html=1, endArrow="block", endSize=10,
            strokeColor=role["stroke"], strokeWidth=TOKENS["stroke_width"], fontColor=TOKENS["text"],
            fontFamily=family, fontSize=profile["edge"], labelBackgroundColor="#FFFFFF",
            exitPerimeter=1, entryPerimeter=1)
        if not model.get("_semantic_generated"):
            options.update(exitX=1, exitY=0.5, entryX=0, entryY=0.5)
        options.update(preset.get("edge_style", {}))
        options.update(edge.get("style", {}))
        if model.get("_semantic_generated") and edge.get("connector_mode") != "fixed":
            for key in ("exitX","exitY","entryX","entryY"):
                options.pop(key,None)
            if edge.get("connector_mode") == "floating":
                for key in ("sourcePortConstraint","targetPortConstraint"):
                    options.pop(key,None)
        if edge.get("points"):
            options.update(edgeStyle="none", noEdgeStyle=1)
        c = cell(edge["id"], edge="1", parent=parent, source=source, target=target,
                 value=edge.get("label", ""), style=style(**options))
        if model.get("_semantic_generated"):
            c.set("pjRole",edge.get("role","data"))
            c.set("pjType",edge.get("type","ordinary"))
        geo = ET.SubElement(c, "mxGeometry", relative="1", x=str(edge.get("label_position", 0)), y=str(edge.get("label_offset", -18)), **{"as": "geometry"})
        if edge.get("points"):
            array = ET.SubElement(geo, "Array", **{"as": "points"})
            for x, y in edge["points"]:
                ET.SubElement(array, "mxPoint", x=str(x), y=str(y))
    if model.get('_semantic_generated'):
        # Native paint order: backgrounds, secondary paths, main paths, foreground
        # nodes. Imported XML and legacy coordinate ordering remain untouched.
        from connector_policy import SECONDARY_ROLES, BACKWARD_TYPES
        edges_by_id={e['id']:e for e in model.get('edges',[])}
        group_ids={g['id'] for g in model.get('groups',[])}
        def paint_priority(c):
            if c.get('id') in ('0','1'):return 0
            if c.get('id') in group_ids:return 1
            if c.get('edge')=='1':
                e=edges_by_id[c.get('id')]
                return 2 if e.get('role') in SECONDARY_ROLES or e.get('type') in BACKWARD_TYPES else 3
            return 4
        root[:]=sorted(root,key=paint_priority)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(file)
    # Bytes keep native source identity stable across Windows/Linux checkouts.
    output.write_bytes(ET.tostring(file, encoding="utf-8", xml_declaration=True))
    if report_path is not None:
        report_path = Path(report_path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report or {"mode": "explicit", "review_flags": ["rendered-qa-required"]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return boxes


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    build(json.loads(args.model.read_text(encoding="utf-8-sig")), args.output, args.report)
